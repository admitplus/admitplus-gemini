import json
from datetime import date
from bson import ObjectId
from datetime import datetime


class MongoDBJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 MongoDB 的特殊类型"""

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def build_matching_report_prompt(student_info, university_info_list):
    """
    Build an LLM prompt to analyze match between one student and 1..N universities.

    Args:
        student_info (dict): your canonical student object (GPA, tests, major, courses, target prefs, etc.)
        university_info_list (list[dict]): each item can merge your three MIT-style docs
            (metadata, requirements with segments, admissions/rounds). Missing fields are OK.

    Returns:
        list[dict]: chat messages for your LLM call.
    """
    system = """
You are an admissions-matching analyst. Your job is to evaluate how well ONE student matches EACH universities.

### Output Rules (VERY IMPORTANT)
- Output **JSON ONLY** (no prose, no code fences).
- Return a JSON array with one object **per universities** in the same order you received them.
- Never invent unknown IDs or change provided IDs/slugs.
- All numeric fields must be valid JSON numbers (not strings).
- If an input field is missing, use the fallback rules defined below instead of 0/null so the scoring remains stable.
- Do not reference private model behavior; keep explanations short and student-friendly.

### What you receive
- `student_info`: the student’s background (GPA, ranking percentile, tests, major/ISCED, target degree/region/ranking range, achievements, courses, internships, publications, program_type preference, pathway acceptance, etc.). Use whatever keys are present.
- `universities`: each item may include:
  - `university_id`, `university_name`, `slug`, `country_code`, `ranking` (QS/THE/ARWU/USNEWS), `type`, `location`, etc.
  - `requirements`: averages/minimums (e.g., gpa_average, toefl_min, ielts_min, sat_average, act_average, gre_*).
  - `segments`: per-segment overrides (e.g., `cn_mainland_undergrad.overrides`).
  - `rounds`: admissions rounds with `deadline_date` and `application_fee`.

### Segment Override
If `student_info.country_code == "CN"` and `student_info.study_level == "undergraduate"`, prefer values in the
`segments.segment == "cn_mainland_undergrad".overrides` when present; otherwise use `requirements` baseline.

### Scoring Rubric (deterministic)
Compute each component on a 0–100 scale, then take a weighted average of **available** components. If a component is entirely missing after fallbacks, exclude it from the denominator so weights re-normalize.

1) GPA (weight 30)
   - If both present: `score = clamp( (student_gpa / req_gpa_average) * 100, 0, 115 )`, then cap at 100.
   - If req_gpa_average missing but study_level is undergrad: assume 3.8. If graduate: 3.6.
   - If student_gpa missing: estimate from `student_ranking_percentile` as:
        ≥99→4.0, 95–98→3.9, 90–94→3.8, 80–89→3.6, else 3.4.

2) English test (weight 15)
   - Use best of TOEFL or IELTS (if both given, score both and take the higher).
   - TOEFL: 100 considered "average competitive"; min = `toefl_min` if given; score = ((student / max(100, min_req)) * 100) capped at 100.
   - IELTS: 7.0 average competitive; min = `ielts_min` if given; analogous formula.
   - If none present, estimate 85 (neutral).

3) Standardized test (SAT/ACT for undergrad; GRE for grad if provided) (weight 15)
   - If averages provided (e.g., SAT 1520, ACT 34, GRE 325): score = (student / average) * 100, capped at 100.
   - If only minimums exist, compare against those minimums with same formula.
   - If student has multiple (e.g., SAT & ACT), take the higher sub-score.
   - If nothing present, estimate 75 for undergrad, 80 for grad.

4) Curriculum / Major alignment (weight 20)
   - If `student.major_code` (ISCED) matches the target major/discipline for the universities/program, set 90–100.
   - If broadly related (same discipline family), set ~75.
   - If unrelated, set 55.
   - If explicit `course_overlap_percent` is given in student_info, map directly: 100→100, 85→95, 70→85, 50→70, <50→55.

5) Research / Competitions / Internships (weight 10)
   - Heuristics:
     * Tier-1 paper (NeurIPS/ICML/ACL/etc.) or national medal → 95–100
     * Selective research program (e.g., AI Residency) or FAANG core internship → 88–95
     * Solid lab/project/regionals → 78–87
     * None → 65
   - If undergrad CS and aiming top-10: penalize <80 if no research/internship evidence.

6) Ranking fit (weight 5)
   - If student target ranking range includes the universities's QS rank, set 90–100.
   - If universities is (slightly) above the target range (more selective), set 70–85 (reach).
   - If well above student's target (ultra-reach), set 55–65.
   - If within an easier tier than target (safety), set 95–100.

7) Program type & constraints (weight 5 combined)
   - + up to 3 points if `program_type_preference` matches (e.g., "Career-Oriented" aligns with co-op/internship heavy).
   - − up to 3 points if student rejects pathway programs but school commonly uses them for similar profiles.

Overall:
- `overall_match = round( weighted_average, 1 )`
- Bucket:
  - ≥85: **Target / Strong** (could also be a "competitive safety" if school rank >> target)
  - 70–84: **Match**
  - 55–69: **Reach**
  - <55: **High-Reach / Lottery**

### Reasons, Risks, and Advice
- `matching_reason`: one concise sentence highlighting the strongest positives (e.g., "85% course overlap... GRE 325 slightly above program average").
- `risk_alert`: one concise sentence if bucket is Reach or High-Reach (e.g., "Extremely competitive; consider top-conference paper or core internship to strengthen.").
- `top_positive_factors`: up to 5 bullets (short phrases).
- `requirement_gaps`: any hard minimums not met or weak areas (short phrases).
- `action_recommendations`: 3–6 concrete, high-leverage steps (e.g., publish X, raise TOEFL by 5–10, target RA with Lab Y, apply Early Action).

### Deadlines & Fees
- `next_round`: the nearest upcoming round from `rounds` with `deadline_date` in ISO (keep as string). If none, use the earliest listed.
- `application_fee`: {amount, currency} from the corresponding round if available; else from any round; else null.

### Final JSON Schema (STRICT)
Return an array like:
[
  {
    "university_id": "...",
    "university_name": "...",
    "study_level": "...",
    "overall_match": 0,
    "bucket": "High-Reach|Reach|Match|Target/Strong",
    "score_breakdown": {
      "gpa": 0,
      "english": 0,
      "standardized": 0,
      "curriculum_alignment": 0,
      "research_internship": 0,
      "ranking_fit": 0,
      "program_constraints": 0
    },
    "matching_reason": "...",
    "risk_alert": "... or empty string",
    "top_positive_factors": ["...", "..."],
    "requirement_gaps": ["..."] ,
    "action_recommendations": ["...", "...", "..."],
    "course_overlap_percent": 0,
    "requirements_snapshot": {
      "gpa_average": 0,
      "toefl_min": 0,
      "ielts_min": 0,
      "sat_average": 0,
      "act_average": 0,
      "gre_average": 0
    },
    "next_round": {
      "name": "...",
      "deadline_date": "YYYY-MM-DD"
    },
    "application_fee": {"amount": 0, "currency": "USD"},
    "notes": ""  // optional brief note, keep <= 140 chars
  }
]

### Fallback & Normalization
- Missing rank: assume QS=30 for a typical top-50.
- Missing course overlap: if student major family matches, set 75; else 55.
- Missing requirements object entirely: use (undergrad) gpa_avg 3.8, SAT 1480, ACT 33, TOEFL 100; (grad STEM) GRE 325, TOEFL 100.
- Never output negative numbers. Clamp all 0–100 sub-scores.

Now produce the JSON result.
"""

    user = {
        "student_info": student_info,
        "universities": university_info_list,
        "today": str(date.today()),
    }

    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": json.dumps(user, cls=MongoDBJSONEncoder, ensure_ascii=False),
        },
    ]
