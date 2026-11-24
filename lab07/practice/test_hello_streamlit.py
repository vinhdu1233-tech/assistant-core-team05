from streamlit.testing.v1 import AppTest


def app():
    return AppTest.from_file("hello_streamlit.py").run()


def test_u1_title():
    assert app().title[0].value == "Hello, Streamlit 👋"


def test_u2_greeting():
    at = app()
    at.text_input[0].input("Lan").run()
    assert at.success[0].value == "Hello, Lan!"


def test_u3_counter_survives_reruns():
    at = app()
    at.button[0].click().run()
    at.button[0].click().run()
    assert "Clicked 2 times" in [m.value for m in at.markdown]


def test_u4_validation():
    at = app()
    at.number_input[0].set_value(32).run()
    assert "advisor approval" in at.error[0].value
    at.number_input[0].set_value(18).run()
    assert "normal load" in at.info[0].value
