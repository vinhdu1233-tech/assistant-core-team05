"""Lab 7 warm-up: a web page in pure Python with Streamlit.

Run:   streamlit run hello_streamlit.py      (a browser tab opens at http://localhost:8501)
Tests: pytest -q test_hello_streamlit.py

Streamlit re-runs this whole file from top to bottom every time the user clicks or types.
Anything you want to REMEMBER between runs must go into st.session_state.
"""
import streamlit as st

st.title("Hello, Streamlit 👋")

# U1 (done): show text
st.write("This page is written in Python only — no HTML needed.")

# U2: a text input and a greeting
name = st.text_input("Your name")
# TODO U2: if name is not empty, show  st.success(f"Hello, {name}!")

# U3: a button and a counter that survives reruns
if "count" not in st.session_state:
    st.session_state.count = 0
if st.button("Click me"):
    pass  # TODO U3: add 1 to st.session_state.count
st.write(f"Clicked {st.session_state.count} times")

# U4: validation — show an error for a bad number of credits
credits = st.number_input("Credits this semester", min_value=0, max_value=40, value=18, step=1)
# TODO U4: if credits > 30 show st.error("More than 30 credits needs advisor approval."),
#          otherwise show st.info(f"{credits} credits is a normal load.")
