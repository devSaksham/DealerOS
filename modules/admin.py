import pandas as pd
import streamlit as st

from core import store

st.title("👤 Users")
st.dataframe(pd.DataFrame([{"username": k, "name": v["name"], "role": v["role"]} for k, v in store.users().items()]),
             hide_index=True, width="stretch")

st.subheader("Add or reset a user")
with st.form("user", clear_on_submit=True):
    c = st.columns(4)
    username = c[0].text_input("Username")
    name = c[1].text_input("Name")
    role = c[2].selectbox("Role", store.ROLES)
    pw = c[3].text_input("Password", type="password")
    if st.form_submit_button("Save", type="primary"):
        if not username.strip() or len(pw) < 6:
            st.error("Need a username and a password of at least 6 characters.")
        else:
            store.save_user(username, name or username, role, pw)
            st.success(f"Saved {username}")
            st.rerun()

st.subheader("Dealership")
s = store.settings()
dealer = st.text_input("Dealership name", s["dealer_name"])
if dealer != s["dealer_name"] and st.button("Save name"):
    store.save_settings({**s, "dealer_name": dealer})
    st.rerun()
