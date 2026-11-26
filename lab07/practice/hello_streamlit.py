"""Lab 7 warm-up: a web page in pure Python with Streamlit.

Run: streamlit run hello_streamlit.py
Tests: pytest -q test_hello_streamlit.py
"""

import streamlit as st

st.title("Hello, Streamlit 👋")

# U1: Show text
st.write("This page is written in Python only — no HTML needed.")

# U2: Text input and greeting
name = st.text_input("Your name")

if name:
    st.success(f"Hello, {name}!")

# U3: Counter that survives reruns
if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("Click me"):
    st.session_state.count += 1

st.write(f"Clicked {st.session_state.count} times")

# U4: Credit validation
credits = st.number_input(
    "Credits this semester",
    min_value=0,
    max_value=40,
    value=18,
    step=1,
)

if credits > 30:
    st.error("More than 30 credits needs advisor approval.")
else:
    st.info(f"{credits} credits is a normal load.")
