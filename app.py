"""DealerOS: one login, one dashboard, a module per department. Run: streamlit run app.py"""
import streamlit as st

from core import i18n, store

st.set_page_config(page_title="DealerOS", page_icon="🏍️", layout="wide")

# Add a department: write modules/<name>.py and add one line here.
MODULES = [
    {"title": "Parts", "page": "modules/parts.py", "icon": "🔧", "roles": ["admin", "parts"]},
    {"title": "Sales", "page": None, "icon": "🏍️", "roles": ["admin", "sales"]},
    {"title": "Service", "page": None, "icon": "🛠️", "roles": ["admin", "service"]},
    {"title": "Users", "page": "modules/admin.py", "icon": "👤", "roles": ["admin"]},
]

lang = st.sidebar.radio("भाषा / Language", list(i18n.LANGS), format_func=i18n.LANGS.get, key="lang")
t = lambda s, **k: i18n.t(s, lang, **k)  # noqa: E731


def login():
    st.title("DealerOS")
    st.caption(f"{store.settings()['dealer_name']} · " + t("dealership dashboard"))
    with st.form("login"):
        username = st.text_input(t("Username"))
        pw = st.text_input(t("Password"), type="password")
        if st.form_submit_button(t("Sign in"), type="primary"):
            user = store.check_login(username, pw)
            if user:
                st.session_state.user = {**user, "username": username.strip().lower()}
                st.rerun()
            st.error(t("Wrong username or password"))
    if store.DEMO:
        st.info(t("Demo logins (password **demo**): `admin`, `parts`, `sales`, `service`. Data is synthetic."))


def coming_soon(title):
    def page():
        st.title(t(title))
        st.info(t("This module is next on the roadmap. Parts came first because shortages hurt most."))
    page.__name__ = title.lower()
    return page


user = st.session_state.get("user")
if not user:
    st.navigation([st.Page(login, title=t("Sign in"))]).run()
    st.stop()

with st.sidebar:
    st.write(f"**{user['name']}** · {t(user['role'])}")
    if st.button(t("Sign out")):
        del st.session_state.user
        st.rerun()

pages = [st.Page(m["page"], title=t(m["title"]), icon=m["icon"]) if m["page"]
         else st.Page(coming_soon(m["title"]), title=t(m["title"]), icon=m["icon"], url_path=m["title"].lower())
         for m in MODULES if user["role"] in m["roles"]]
st.navigation(pages).run()
