from typing import List, Dict


def build_generate_report_prompt(
    student_profile: Dict, university_info_list: List[Dict]
) -> List[Dict[str, str]]:
    system_prompt = (
        "You are an expert admissions advisor who helps students evaluate potential universities.\n"
        "Given a students's background and a list of universities information, generate a reports that includes:\n"
        "1. A short introduction for each universities (based on the provided information)\n"
        "2. A reflection on how well the students fits each school's academic strengths (especially major/program alignment)\n"
        "3. An estimated admission chance for each universities:\n"
        "   • 'High Safety' – very likely to get in\n"
        "   • 'Match' – reasonable chance\n"
        "   • 'Reach' – challenging but possible\n"
        "   • 'Unlikely' – very hard to get in\n\n"
        "Use a professional tone. Structure the output as a clear, multi-section reports."
    )

    # Format the students profile for display
    user_prompt = "Student Profile:\n"
    for key, value in student_profile.items():
        pretty_key = key.replace("_", " ").capitalize()
        user_prompt += f"- {pretty_key}: {value}\n"

    # List universities to be evaluated
    user_prompt += "\nEvaluate the following universities:\n"
    for idx, university in enumerate(university_info_list, start=1):
        # Extract universities name from the universities info
        university_name = university.get(
            "name", university.get("university_name", f"University {idx}")
        )
        user_prompt += f"{idx}. {university_name}\n"

        # Add additional universities information if available
        if university.get("location"):
            user_prompt += f"   Location: {university.get('location')}\n"
        if university.get("type"):
            user_prompt += f"   Type: {university.get('type')}\n"
        if university.get("admission", {}).get("gpa", {}).get("average"):
            user_prompt += f"   Average GPA: {university.get('admission', {}).get('gpa', {}).get('average')}\n"
        user_prompt += "\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
