import re


def clarify_thesis_eligibility(question: str, answer: str) -> str:
    """Add a direct credit-based conclusion to thesis eligibility answers."""
    question_lower = question.lower()
    answer_lower = answer.lower()

    is_thesis_question = "thesis" in question_lower and (
        "register" in question_lower or "registration" in question_lower
    )

    if not is_thesis_question:
        return answer

    student_match = re.search(
        r"\b(\d{1,3})\s+credits?\b",
        question_lower,
    )
    minimum_match = re.search(
        r"at least\s+(\d{1,3})\s+accumulated credits",
        answer_lower,
    )

    if not student_match or not minimum_match:
        return answer

    student_credits = int(student_match.group(1))
    minimum_credits = int(minimum_match.group(1))

    if student_credits >= minimum_credits:
        return answer

    missing_credits = minimum_credits - student_credits

    conclusion = (
        f"**Not eligible yet based on credits:** "
        f"{student_credits} credits is {missing_credits} credits "
        f"below the {minimum_credits}-credit minimum."
    )

    return f"{conclusion}\n\n{answer}"
