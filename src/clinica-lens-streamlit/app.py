import streamlit as st

import api_client as api

st.set_page_config(page_title="Clinica-lens", page_icon="🩺", layout="centered")


# ---------------------------------------------------------------- state ----
def _new_conversation() -> None:
    st.session_state.thread_id = None
    st.session_state.messages = []


def _open_conversation(thread_id: str) -> None:
    st.session_state.thread_id = thread_id
    # History always comes from the server, never from local state.
    st.session_state.messages = api.get_messages(st.session_state.token, thread_id)


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

# ---------------------------------------------------------------- streaming ----


def run_turn(token: str, question: str, thread_id: str):
    answer, steps, failed = "", [], False

    with st.chat_message("assistant"):
        steps_box = st.container()  # sits above the answer
        text = st.empty()
        text.markdown("_thinking…_")
        status = None  # created only if a tool is actually used

        try:
            for name, data in api.stream_answer(token, question, thread_id):
                if name in ("tool_call", "tool_result"):
                    if status is None:
                        status = steps_box.status("Working…", expanded=True)
                    if name == "tool_call":
                        line = f"🔧 **{data.get('name', '')}**"
                        status.update(label=f"Running {data.get('name', '')}…")
                    else:
                        line = f"✅ {data.get('name', '')} → {data.get('status', '')}"
                    steps.append(line)
                    status.write(line)

                elif name == "token":
                    answer += data["text"]
                    text.markdown(answer + "▌")

                elif name == "error":
                    failed = True
                    answer += f"\n\n**Error {data.get('error_code', '')}:** {data.get('message', data)}"
                    break

                elif name == "done":
                    break

        except api.AuthError as e:
            _logout(str(e))
        except api.ApiError as e:
            failed = True
            answer = answer or f"Something went wrong: {e}"

        text.markdown(answer or "_No answer was returned._")
        if status is not None:
            status.update(
                label=f"Used {len(steps) // 2 or 1} tool(s)",
                state="error" if failed else "complete",
                expanded=False,
            )

    return answer, steps, failed


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
        active = c["thread_id"] == st.session_state.thread_id
        st.button(
            (c.get("title") or c["thread_id"][:8])[:40],
            key=f"conv-{c['thread_id']}",
            use_container_width=True,
            type="secondary" if not active else "primary",
            on_click=_open_conversation,
            args=(c["thread_id"],),
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

for m in st.session_state.messages:
    if m["content"] == "" or m["role"] == "tool":
        continue
    with st.chat_message(m["role"]):
        if m["role"] == "assistant":
            if m.get("steps"):
                with st.status(
                    f"Used {len(m['steps']) // 2 or 1} tool(s)",
                    state="complete",
                    expanded=False,
                ):
                    for line in m["steps"]:
                        st.write(line)
        st.markdown(m["content"])

if question := st.chat_input("Ask a question"):
    if st.session_state.thread_id is None:
        try:
            st.session_state.thread_id = api.create_conversation(token)
        except api.AuthError as e:
            _logout(str(e))
        except api.ApiError as e:
            st.error(str(e))
            st.stop()
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    answer, steps, failed = run_turn(token, question, st.session_state.thread_id)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "steps": steps}
    )
    st.rerun() if not failed else None  # refresh the sidebar conversation list
