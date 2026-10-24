"""
app.py  —  OWNER: AliMoR10
The web page (Streamlit). Run with:  streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import os  # noqa: E402

import gemma  # noqa: E402
import github_api  # noqa: E402

st.set_page_config(page_title="First PR Buddy", page_icon="🤝", layout="wide")

EXAMPLES = {
    "🌱 First Contributions": "https://github.com/firstcontributions/first-contributions",
    "🎈 Streamlit": "https://github.com/streamlit/streamlit",
    "🏕️ freeCodeCamp": "https://github.com/freeCodeCamp/freeCodeCamp",
}


def use_example(link):
    st.session_state.url = link
    st.session_state.auto_run = True


def show_error(e):
    """Turn technical errors into friendly messages (details stay available)."""
    msg = str(e)
    if "Ollama" in msg:
        st.error(f"💻 {msg}")
    elif "API key" in msg or "GEMINI_API_KEY" in msg:
        st.error("🔑 Gemma couldn't use the API key. Paste a valid key under ⚙️ Settings in the sidebar.")
    elif any(code in msg for code in ("500", "502", "503", "504", "INTERNAL", "UNAVAILABLE")):
        st.warning("☁️ Google's Gemma servers are having a moment. We retried a few times. Please try again in a minute.")
    elif "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
        st.warning("⏳ Gemma is busy right now (usage limit). Wait a minute and try again.")
    elif "rate limit" in msg.lower():
        st.warning("⏳ GitHub's limit was reached. Add a GITHUB_TOKEN to your .env file to raise it.")
    elif isinstance(e, ValueError):
        st.warning(f"🤔 {msg}")
    else:
        st.error("😕 Something went wrong. Please try again.")
    with st.expander("Technical details"):
        st.code(msg)


with st.sidebar:
    st.header("🤝 How it works")
    st.markdown(
        "1. **Paste** a GitHub repo link\n"
        "2. **Understand** the project in plain English\n"
        "3. **Pick** a beginner-friendly issue\n"
        "4. **Follow** your step-by-step plan to a pull request\n\n"
        "Stuck? Upload a **screenshot** of your error, or **ask Buddy** anything."
    )
    st.subheader("Try an example")
    for label, link in EXAMPLES.items():
        st.button(label, on_click=use_example, args=(link,), use_container_width=True)
    st.divider()
    with st.expander("⚙️ Settings", expanded=False):
        where = st.radio(
            "Where should Gemma 4 run?",
            ["☁️ Cloud (Gemini API)", "💻 On my computer (Ollama)"],
            index=1 if os.getenv("GEMMA_BACKEND") == "ollama" else 0,
            help="On your computer = free, private and offline. Needs Ollama installed and `ollama pull gemma4`.",
        )
        backend = "ollama" if where.startswith("💻") else "gemini"
        user_key = None
        if backend == "gemini":
            if os.getenv("GEMINI_API_KEY"):
                st.caption("✅ Using the app's built-in key. You can also use your own:")
            user_key = st.text_input(
                "Your Gemini API key (optional)",
                type="password",
                help="Get a free key at aistudio.google.com/apikey",
            ).strip() or None
            st.caption("🔒 Your key is only used for this session. It is never saved or shared.")
        else:
            st.caption("Only works when you run this app on your own computer with the Ollama app open.")
    gemma.configure(api_key=user_key, backend=backend)
    if st.session_state.get("backend") != backend:  # switching engines starts a fresh chat
        st.session_state.backend = backend
        st.session_state.chat = None
    st.divider()
    st.caption("Powered by **Gemma 4**, Google's open model · Hosted on **DigitalOcean**")
    st.caption("[View source on GitHub](https://github.com/AliMoR10/MLH-Hackathon)")

st.title("🤝 First PR Buddy")
st.caption("Paste any GitHub repo. Get a friendly guide to your first open-source contribution. Powered by Gemma 4.")

url = st.text_input("GitHub repo link", key="url", placeholder="https://github.com/owner/repo")
clicked = st.button("Explain this repo", type="primary")
auto_run = st.session_state.pop("auto_run", False)

if (clicked or auto_run) and url:
    try:
        owner, repo = github_api.parse_repo_url(url)
        with st.spinner("📥 Reading the repo from GitHub..."):
            info = github_api.get_repo_info(owner, repo)
            readme = github_api.get_readme(owner, repo)
            files = github_api.get_file_tree(owner, repo, info["default_branch"])
            issues = github_api.get_beginner_issues(owner, repo)
        with st.spinner("🧠 Gemma 4 is studying the code... (about 10 seconds)"):
            summary = gemma.summarize_repo(info, readme, files)
        st.session_state.update(
            info=info, readme=readme, files=files, issues=issues, summary=summary,
            plans={}, chat=None, messages=[],
        )
    except Exception as e:
        show_error(e)

if "info" not in st.session_state:
    st.info("👋 New to open source? Paste a repo link above, or pick an example in the sidebar to see how it works.")
else:
    info = st.session_state.info
    st.subheader(f"📦 {info['name']}")
    st.write(f"⭐ {info['stars']}  ·  {info['language']}  ·  [Open on GitHub]({info['url']})")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["What is this project?", "Where can I help?", "Stuck on an error?", "Ask Buddy"]
    )

    with tab1:
        st.markdown(st.session_state.summary)

    with tab2:
        issues = st.session_state.issues
        if not issues:
            st.info("No issues labelled 'good first issue' or 'help wanted' right now. Try another repo!")
        for issue in issues:
            with st.expander(f"#{issue['number']}  {issue['title']}"):
                st.write(f"[View issue on GitHub]({issue['url']})")
                key = f"plan_{issue['number']}"
                if st.button("Make me a plan", key=key):
                    with st.spinner("Gemma 4 is planning your first PR..."):
                        try:
                            st.session_state.plans[key] = gemma.plan_for_issue(
                                info, st.session_state.files, issue
                            )
                        except Exception as e:
                            show_error(e)
                if key in st.session_state.plans:
                    st.markdown(st.session_state.plans[key])

    with tab3:
        shot = st.file_uploader("Upload a screenshot of your error", type=["png", "jpg", "jpeg"])
        if shot and st.button("Explain this error"):
            with st.spinner("Gemma 4 is looking at your screenshot..."):
                try:
                    st.markdown(gemma.explain_screenshot(shot.getvalue(), shot.type, info))
                except Exception as e:
                    show_error(e)

    with tab4:
        st.write("Ask anything about this repo, e.g. *Where are the tests?* or *What does this folder do?*")
        for role, text in st.session_state.messages:
            with st.chat_message(role):
                st.markdown(text)
        question = st.chat_input("Ask First PR Buddy...")
        if question:
            st.session_state.messages.append(("user", question))
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"), st.spinner("Thinking..."):
                try:
                    if st.session_state.chat is None:
                        st.session_state.chat = gemma.start_chat(
                            info, st.session_state.readme, st.session_state.files
                        )
                    answer = gemma.ask_chat(st.session_state.chat, question)
                    st.markdown(answer)
                    st.session_state.messages.append(("assistant", answer))
                except Exception as e:
                    show_error(e)

st.divider()
st.caption("Open source (MIT) · Built at MLH Hacktoberfest 2026 · Gemma 4 + DigitalOcean")
