import pandas as pd
import streamlit as st

from core import i18n, report, store

lang = st.session_state.get("lang", "en")
t = lambda s, **k: i18n.t(s, lang, **k)  # noqa: E731

st.title("👤 " + t("Users"))
st.dataframe(pd.DataFrame([{t("Username"): k, t("Name"): v["name"], t("Role"): t(v["role"])}
                           for k, v in store.users().items()]), hide_index=True, width="stretch")

if store.DEMO:
    st.info(t("User, email and dealership settings are read-only in the public demo."))
    st.stop()

st.subheader(t("Add or reset a user"))
with st.form("user", clear_on_submit=True):
    c = st.columns(4)
    username = c[0].text_input(t("Username"))
    name = c[1].text_input(t("Name"))
    role = c[2].selectbox(t("Role"), store.ROLES, format_func=t)
    pw = c[3].text_input(t("Password"), type="password")
    if st.form_submit_button(t("Save"), type="primary"):
        if not username.strip() or len(pw) < 6:
            st.error(t("Need a username and a password of at least 6 characters."))
        else:
            store.save_user(username, name or username, role, pw)
            st.success(t("Saved {name}", name=username))
            st.rerun()

s = store.settings()
st.subheader(t("Daily report by email"))
st.caption(t("Email login status: {status}", status=t("ready") if report.email_ready() else t("not set up")))
if not report.email_ready():
    st.code('SMTP_HOST = "smtp.gmail.com"\nSMTP_PORT = "465"\nSMTP_USER = "you@gmail.com"\n'
            'SMTP_PASSWORD = "<16-letter Gmail app password>"', language="toml")
    st.caption(t("Put these in .streamlit/secrets.toml on this computer (or in the app's Secrets on Streamlit Cloud)."))
emails = st.text_area(t("Send the report to (one email per line)"), "\n".join(s["report_emails"]))
rlang = st.radio(t("Report language"), list(i18n.LANGS), format_func=i18n.LANGS.get, horizontal=True,
                 index=list(i18n.LANGS).index(s["report_lang"]))
if st.button(t("Save email settings")):
    to = [e.strip() for e in emails.splitlines() if e.strip()]
    bad = [e for e in to if not report.EMAIL_RE.match(e)]
    if bad:
        st.error(t("Not a valid email: {e}", e=", ".join(bad)))
    else:
        store.save_settings({**s, "report_emails": to, "report_lang": rlang})
        st.success(t("Saved"))

st.subheader(t("Dealership"))
dealer = st.text_input(t("Dealership name"), s["dealer_name"])
if dealer != s["dealer_name"] and st.button(t("Save name")):
    store.save_settings({**s, "dealer_name": dealer})
    st.rerun()
