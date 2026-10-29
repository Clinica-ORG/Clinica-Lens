import uuid

import streamlit as st

import api_client as api

st.set_page_config(page_title="Clinica-lens", page_icon="🩺", layout="centered")


# ---------------------------------------------------------------- state ----
def _new_conversation() -> None:
    st.session_state.conv_id = str(uuid.uuid4())
    st.session_state.messages = []


def _open_conversation(conv_id: str) -> None:
    st.session_state.conv_id = conv_id
    # History always comes from the server, never from local state.
    st.session_state.messages = api.get_messages(st.session_state.token, conv_id)


def _logout(message: str | None = None) -> None:
    st.session_state.clear()  # nothing from this user survives in the session
    if message:
        st.session_state.login_notice = message
    st.rerun()


# ---------------------------------------------------------------- login ----
def login_view() -> None:
    st.title("Clinica-lens")
    if notice := st.session_state.pop("login_notice", None):
        st.warning(notice)
    with st.form("login"):
        user_name = st.text_input("User name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if not submitted:
        return
    if not user_name or not password:
        st.error("Enter your user name and password.")
        return
    try:
        token = api.login(user_name, password)
    except api.AuthError as e:
        st.error(str(e))
        return
    except api.ApiError as e:
        st.error(str(e))
        return
    st.session_state.token = token
    st.session_state.user_name = user_name
    _new_conversation()
    st.rerun()


if "token" not in st.session_state:
    login_view()
    st.stop()

token: str = st.session_state.token

# -------------------------------------------------------------- sidebar ----
try:
    conversations = api.list_conversations(token)
except api.AuthError as e:
    _logout(str(e))

with st.sidebar:
    st.markdown(f"**{st.session_state.user_name}**")
    if st.button("Log out", use_container_width=True):
        _logout()
    st.divider()
    st.button(
        "＋ New conversation",
        type="primary",
        use_container_width=True,
        on_click=_new_conversation,
    )
    if not conversations:
        st.caption("No conversations yet.")
    for c in conversations:
        active = c["id"] == st.session_state.conv_id
        st.button(
            (c.get("title") or c["id"][:8])[:40],
            key=f"conv-{c['id']}",
            use_container_width=True,
            type="secondary" if not active else "primary",
            on_click=_open_conversation,
            args=(c["id"],),
        )

# ----------------------------------------------------------------- chat ----
st.title("Clinica-lens")

if not st.session_state.messages:
    st.caption(
        "Ask a question about your clinical data. Answers use read-only queries."
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if question := st.chat_input("Ask a question"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_thinking…_")
        answer = ""
        failed = False
        try:
            for event in api.stream_answer(token, question, st.session_state.conv_id):
                if "token" in event:
                    answer += event["token"]
                    placeholder.markdown(answer + "▌")
                elif "status" in event and not answer:
                    placeholder.markdown(f"_{event['status']}…_")
                elif "error" in event:
                    failed = True
                    break
        except api.AuthError as e:
            _logout(str(e))
        except api.ApiError as e:
            failed = True
            answer = answer or str(e)

        if failed and not answer:
            answer = "Something went wrong. Please try again."
        placeholder.markdown(answer)
        if failed:
            st.error("The answer may be incomplete.", icon="⚠️")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun() if not failed else None  # refresh the sidebar conversation list
