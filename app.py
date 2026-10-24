"""
app.py  —  OWNER: AliMoR10
The web page (Streamlit). Run with:  streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import gemma  # noqa: E402
import github_api  # noqa: E402

st.set_page_config(page_title="First PR Buddy", page_icon="🤝", layout="wide")

st.title("🤝 First PR Buddy")
st.caption("Paste any GitHub repo. Get a friendly guide to your first open-source contribution. Powered by Gemma 4.")

url = st.text_input("GitHub repo link", placeholder="https://github.com/owner/repo")

if st.button("Explain this repo", type="primary") and url:
    try:
        owner, repo = github_api.parse_repo_url(url)
        with st.spinner("Reading the repo from GitHub..."):
            info = github_api.get_repo_info(owner, repo)
            readme = github_api.get_readme(owner, repo)
            files = github_api.get_file_tree(owner, repo, info["default_branch"])
            issues = github_api.get_beginner_issues(owner, repo)
        with st.spinner("Gemma 4 is studying the code..."):
            summary = gemma.summarize_repo(info, readme, files)
        st.session_state.update(
            info=info, readme=readme, files=files, issues=issues, summary=summary,
            plans={}, chat=None, messages=[],
        )
    except Exception as e:
        #TODO Ask user for key and automatically add to .env
        st.error(str(e))

if "info" in st.session_state:
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
                            st.error(str(e))
                if key in st.session_state.plans:
                    st.markdown(st.session_state.plans[key])

    with tab3:
        shot = st.file_uploader("Upload a screenshot of your error", type=["png", "jpg", "jpeg"])
        if shot and st.button("Explain this error"):
            with st.spinner("Gemma 4 is looking at your screenshot..."):
                try:
                    st.markdown(gemma.explain_screenshot(shot.getvalue(), shot.type, info))
                except Exception as e:
                    st.error(str(e))

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
                    st.error(str(e))

st.divider()
st.caption("Open source (MIT) · Built at MLH Hacktoberfest 2026 · Gemma 4 + DigitalOcean")
