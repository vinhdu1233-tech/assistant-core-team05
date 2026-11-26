from ui.presentation import clarify_thesis_eligibility


def test_two_credit_counts_do_not_infer_a_shortfall():
    question = "I took 18 credits this semester and have 118 credits in total. Can I register my thesis?"
    answer = "You need at least 120 accumulated credits."
    assert clarify_thesis_eligibility(question, answer) == answer


def test_thesis_answer_explains_missing_credits():
    question = "Can I register my thesis with 118 credits?"
    answer = (
        "According to 5.3 Thesis registration: Students may register "
        "a thesis when they have at least 120 accumulated credits "
        "and a cumulative GPA of at least 2.0."
    )

    result = clarify_thesis_eligibility(question, answer)

    assert "**Not eligible yet based on credits:**" in result
    assert "118 credits is 2 credits below the 120-credit minimum." in result
    assert "cumulative GPA of at least 2.0" in result


def test_non_thesis_answer_is_unchanged():
    question = "Where can I replace my lost student card?"
    answer = "A lost student card can be replaced at Student Affairs."

    assert clarify_thesis_eligibility(question, answer) == answer


def test_answer_without_credit_threshold_is_unchanged():
    question = "Can I register my thesis with 118 credits?"
    answer = "Please contact the Training Office for confirmation."

    assert clarify_thesis_eligibility(question, answer) == answer
