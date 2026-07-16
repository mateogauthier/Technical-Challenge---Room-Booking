import streamlit as st
from src.auth import authenticate
from src.booking_store import init_db
from src.agent import build_agent, run_agent

st.set_page_config(page_title="Room Booking Assistant", page_icon="🏢")

init_db()


def show_login() -> None:
    st.title("Room Booking Assistant")
    st.subheader("Cubo Itaú — Meeting Room Chatbot")
    st.divider()

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if authenticate(username, password):
            st.session_state.user = username
            st.session_state.messages = []
            st.session_state.agent = build_agent(username)
            st.rerun()
        else:
            st.error("Invalid username or password.")


def show_chat() -> None:
    user = st.session_state.user

    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("Room Booking Assistant")
        st.caption(f"Logged in as **{user}**")
    with col2:
        if st.button("Log out"):
            for key in ("user", "messages", "agent"):
                st.session_state.pop(key, None)
            st.rerun()

    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("How can I help you book a room?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = run_agent(
                    st.session_state.agent,
                    prompt,
                    st.session_state.messages[:-1],
                    user,
                )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if "user" not in st.session_state:
    show_login()
else:
    show_chat()
