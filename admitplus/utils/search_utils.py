import json
import logging

from app.llm.prompts.tools_prompts import (
    build_location_parser_prompt,
    build_parser_university_type,
    build_gpa_parser_prompt,
    build_multi_language_parser_prompt,
    build_sat_parser_prompt,
    build_budget_parser_prompt,
)


def search_universities_by_type(student_input: str, university_list):
    try:
        prompt = build_parser_university_type(student_input)
        university_types = call_openai(prompt)
        if isinstance(university_types, str):
            university_types = [university_types]
        target_types = set(t.lower().strip() for t in university_types)
        logging.info(
            f"[Type Filter] LLM returned: {university_types}, target_types: {target_types}"
        )
        for university in university_list:
            logging.info(
                f"[Type Filter] {university.get('name', '')} type: {university.get('type', '')}"
            )
        include_university = [
            u
            for u in university_list
            if u.get("type", "").lower().strip() in target_types
        ]
        logging.info(f"[Type Filter] Matched {len(include_university)} universities.")
        return include_university
    except Exception as e:
        logging.error(f"Error in search_universities_by_type: {e}")
        return university_list


def search_universities_by_gpa(student_input: str, university_list):
    try:
        prompt = build_gpa_parser_prompt(student_input)
        response_text = call_openai(prompt)
        logging.info(f"[GPA Filter] Raw LLM response: {response_text}")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
        if not response_text or response_text.lower() == "null":
            logging.info("[GPA Filter] No GPA extracted from input.")
            return university_list
        response = json.loads(response_text)
        student_gpa = response.get("gpa")
        if student_gpa is None:
            logging.info("[GPA Filter] GPA is None after parsing.")
            return university_list
        adjusted_gpa = min(student_gpa + 0.3, 4.0)
        logging.info(
            f"[GPA Filter] Student GPA: {student_gpa}, Adjusted GPA: {adjusted_gpa}"
        )
        include_university = []
        for u in university_list:
            try:
                avg_gpa = u["admission"]["undergraduate"]["gpa"]["average"]
                if avg_gpa is not None and avg_gpa <= adjusted_gpa:
                    include_university.append(u)
                    logging.debug(
                        f"[GPA Filter] Added: {u.get('name', '')} GPA: {avg_gpa}"
                    )
            except Exception as e:
                logging.debug(f"[GPA Filter] Skipped: {u.get('name', '')} due to {e}")
        logging.info(f"[GPA Filter] Matched {len(include_university)} universities.")
        return include_university
    except Exception as e:
        logging.error(f"Error in search_universities_by_gpa: {e}")
        return university_list


def search_universities_by_sat(student_input: str, university_list):
    try:
        prompt = build_sat_parser_prompt(student_input)
        response_text = call_openai(prompt)
        logging.info(f"[SAT Filter] Raw LLM response: {response_text}")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
        if not response_text or response_text.lower() == "null":
            logging.info("[SAT Filter] No SAT extracted from input.")
            return university_list
        response = json.loads(response_text)
        sat_score = response.get("sat")
        if sat_score is None:
            logging.info("[SAT Filter] SAT is None after parsing.")
            return university_list
        adjusted_sat = min(sat_score + 200, 1600)
        logging.info(
            f"[SAT Filter] Student SAT: {sat_score}, Adjusted SAT: {adjusted_sat}"
        )
        include_university = []
        for u in university_list:
            try:
                sat_range = u["admission"]["undergraduate"]["sat_range"]
                sat_low = sat_range[0] if sat_range else None
                if sat_low is not None and sat_low <= adjusted_sat:
                    include_university.append(u)
                    logging.debug(
                        f"[SAT Filter] Added: {u.get('name', '')} SAT: {sat_low}"
                    )
            except Exception as e:
                logging.debug(f"[SAT Filter] Skipped: {u.get('name', '')} due to {e}")
        logging.info(f"[SAT Filter] Matched {len(include_university)} universities.")
        return include_university
    except Exception as e:
        logging.error(f"Error in search_universities_by_sat: {e}")
        return university_list


def search_universities_by_language(student_input: str, university_list):
    try:
        prompt = build_multi_language_parser_prompt(student_input)
        response_text = call_openai(prompt)
        logging.info(f"[Language Filter] Raw LLM response: {response_text}")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
        if not response_text or response_text.lower() == "null":
            logging.info("[Language Filter] No language score extracted from input.")
            return university_list
        response = json.loads(response_text)
        test_type = response.get("type")
        test_score = response.get("score")
        if not test_type or test_score is None:
            logging.info("[Language Filter] type or score is None after parsing.")
            return university_list
        matched_universities = []
        for u in university_list:
            try:
                lang_req = u["admission"]["requirements"]["language"]
                test_info = lang_req.get(test_type.lower())
                if test_info and test_info.get("accept", False):
                    min_score = test_info.get("min", 0)
                    if test_score >= min_score:
                        matched_universities.append(u)
                        logging.debug(
                            f"[Language Filter] Added: {u.get('name', '')} {test_type}: {test_score}"
                        )
            except Exception as e:
                logging.debug(
                    f"[Language Filter] Skipped: {u.get('name', '')} due to {e}"
                )
        logging.info(
            f"[Language Filter] Matched {len(matched_universities)} universities."
        )
        return matched_universities
    except Exception as e:
        logging.error(f"Error in search_universities_by_language: {e}")
        return university_list


def search_universities_by_budget(student_input: str, university_list):
    try:
        prompt = build_budget_parser_prompt(student_input)
        response_text = call_openai(prompt)
        logging.info(f"[Budget Filter] Raw LLM response: {response_text}")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
        if not response_text or response_text.lower() == "null":
            logging.info("[Budget Filter] No budget extracted from input.")
            return university_list
        response = json.loads(response_text)
        budget_amount = response.get("budget")
        if budget_amount is None:
            logging.info("[Budget Filter] budget is None after parsing.")
            return university_list
        buffer = 5000.0
        max_budget = budget_amount + buffer
        include_university = []
        for u in university_list:
            try:
                tuition = u["tuition_and_aid"]["undergraduate"]["out_of_state_tuition"]
                if tuition is not None and tuition <= max_budget:
                    include_university.append(u)
                    logging.debug(
                        f"[Budget Filter] Added: {u.get('name', '')} tuition: {tuition}"
                    )
            except Exception as e:
                logging.debug(
                    f"[Budget Filter] Skipped: {u.get('name', '')} due to {e}"
                )
        logging.info(f"[Budget Filter] Matched {len(include_university)} universities.")
        return include_university
    except Exception as e:
        logging.error(f"Error in search_universities_by_budget: {e}")
        return university_list


def search_universities_by_location_preference(student_input: str, university_list):
    try:
        prompt = build_location_parser_prompt(student_input)
        response_text = call_openai(prompt)
        logging.info(f"[Location Filter] Raw LLM response: {response_text}")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
        if not response_text or response_text.lower() == "null":
            logging.info("[Location Filter] No location extracted from input.")
            return university_list
        response = json.loads(response_text)
        REGION_STATE_MAPPING = {
            "west": [
                "California",
                "Washington",
                "Oregon",
                "Nevada",
                "Arizona",
                "Utah",
                "Colorado",
                "New Mexico",
            ],
            "east": [
                "New York",
                "Massachusetts",
                "New Jersey",
                "Pennsylvania",
                "Maryland",
            ],
            "south": ["Texas", "Florida", "Georgia", "North Carolina"],
            "midwest": ["Illinois", "Ohio", "Michigan", "Minnesota", "Indiana"],
        }

        def get_region_by_state(state: str) -> str:
            for region, states in REGION_STATE_MAPPING.items():
                if state in states:
                    return region
            return ""

        def calculate_location_score(school: dict, location_preferences: dict) -> int:
            score = 0
            state = school.get("state", "")
            city = school.get("city", "")
            if state in location_preferences.get("states", []):
                score += 10
            if get_region_by_state(state) in location_preferences.get("regions", []):
                score += 5
            if city in location_preferences.get("cities", []):
                score += 15
            return score

        scored_universities = []
        for u in university_list:
            try:
                score = calculate_location_score(u, response)
                if score > 0:
                    scored_universities.append((u, score))
                    logging.debug(
                        f"[Location Filter] Added: {u.get('name', '')} score: {score}"
                    )
            except Exception as e:
                logging.debug(
                    f"[Location Filter] Skipped: {u.get('name', '')} due to {e}"
                )
        scored_universities.sort(key=lambda x: x[1], reverse=True)
        result = [uni for uni, score in scored_universities]
        logging.info(f"[Location Filter] Matched {len(result)} universities.")
        return result
    except Exception as e:
        logging.error(f"Error in search_universities_by_location_preference: {e}")
        return university_list
