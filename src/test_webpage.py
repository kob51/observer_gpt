import streamlit as st
from openai import OpenAI

# 1. Setup the UI
st.set_page_config(page_title="Observer-GPT", page_icon="🥏")
st.title("🥏 Observer-GPT")
st.caption("Describe what happened on the field, and Observer-GPT will tell you the ruling!")

# 2. Rule Selection
ruleset = st.radio("Rulebook:", ["USAU", "WFDF"], horizontal=True)

# 3. Initialize Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle Logic
if prompt := st.chat_input("What happened?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # This is where you'd connect to your Rules Database
    response = f"Under {ruleset}, that is a foul. (Simulated response)"
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})