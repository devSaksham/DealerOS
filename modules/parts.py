import datetime as dt
import re

import pandas as pd
import streamlit as st

from core import forecast as F
from core import store

user = st.session_state.user
s = store.settings()
today = dt.date.today()


@st.cache_data
def compute(stamp_):
    """Refit on every change to the data files (stamp_ = their modified times)."""
    h, d = store.history(), store.daily()
    return h, d, F.forecast(h, d)


def stamp():
    return tuple(p.stat().st_mtime if p.exists() else 0 for p in (store.HISTORY, store.DAILY))


h, d, fc = compute(stamp())
last_month = h.month.max()
open_lost = d[(d.kind == "lost") & (d.date.str[:7] > last_month)].groupby("part").qty.sum()
orders = F.reorder(fc, s["lead_days"], s["review_days"], s["z"], open_lost)
label = lambda p: f"{p} · {fc.desc.get(p, '')}"  # noqa: E731

st.title("🔧 Parts")
st.caption(f"Demand history up to **{last_month}** · {len(fc):,} parts · forecast refits whenever data changes")

tabs = st.tabs(["Order list", "Counter log", "Part trend", "Daily report", "Dead stock", "Upload HiRise", "Accuracy"])

with tabs[0]:
    c = st.columns(4)
    c[0].metric("Lines to order", f"{len(orders):,}")
    c[1].metric("Order value", f"₹{orders.order_value.sum():,.0f}")
    c[2].metric("Out of stock / runs out in 7 days",
                f"{int((orders.stock <= 0).sum())} / {int(((orders.stock > 0) & (orders.days_left <= 7)).sum())}")
    c[3].metric("Lost sales logged (open)", int(open_lost.sum()))
    with st.expander("Ordering settings"):
        lead = st.number_input("Days from order to delivery (Honda lead time)", 1, 90, s["lead_days"])
        review = st.number_input("Days between orders", 1, 60, s["review_days"])
        z = st.select_slider("Safety level", [1.0, 1.28, 1.65, 2.05], s["z"],
                             format_func=lambda v: {1.0: "Lean (84%)", 1.28: "Normal (90%)",
                                                    1.65: "Safe (95%)", 2.05: "Very safe (98%)"}[v])
        if st.button("Save settings"):
            store.save_settings({**s, "lead_days": lead, "review_days": review, "z": z})
            st.rerun()
    show = orders.reset_index()[["part", "desc", "category", "stock", "rate", "days_left", "order", "price", "order_value"]]
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "part": "Part no.", "desc": "Description", "stock": "In stock",
        "rate": st.column_config.NumberColumn("Sells / month", format="%.1f"),
        "days_left": st.column_config.NumberColumn("Days left", help="At the current sales pace"),
        "order": "Order qty", "price": st.column_config.NumberColumn("Unit ₹", format="%.0f"),
        "order_value": st.column_config.NumberColumn("Value ₹", format="%.0f")})
    st.download_button("Download order list (CSV)", show.to_csv(index=False), f"order_{today}.csv")

with tabs[1]:
    st.write("Say what happened at the counter. Hold your Wispr key and talk, or type.")
    said = st.text_input("Example: customer wanted 2 brake shoes, we didn't have them", key="said")
    words = [w.rstrip("s") if len(w) > 3 else w for w in re.findall(r"[a-z0-9-]+", said.lower()) if len(w) > 2]
    text = pd.Series(fc.index.str.lower(), index=fc.index) + " " + fc.desc.fillna("").str.lower()
    score = sum(text.str.contains(re.escape(w)).astype(int) for w in words) if words else None
    matches = list(score[score > 0].sort_values(ascending=False).index[:10]) if words else []
    qty_said = next((int(n) for n in re.findall(r"\b\d{1,3}\b", said)), 1)
    lost_words = any(w in said.lower() for w in ("didn't", "did not", "not available", "out of stock", "wanted", "nahi"))
    with st.form("log", clear_on_submit=True):
        part = st.selectbox("Part", matches or list(fc.index), format_func=label,
                            help="Best matches for what you said come first")
        cols = st.columns(3)
        qty = cols[0].number_input("Qty", 1, 999, qty_said)
        kinds = {"lost": "Lost sale (we didn't have it)", "sale": "Sold", "received": "Received from Honda"}
        kind = cols[1].radio("What happened", list(kinds), format_func=kinds.get, index=0 if lost_words else 1)
        date = cols[2].date_input("Date", today)
        if st.form_submit_button("Save", type="primary"):
            store.add_daily(date, part, qty, kind, said, user["username"])
            st.session_state.flash = f"Saved: {kinds[kind].split(' (')[0]} · {qty} × {label(part)}"
            del st.session_state["said"]
            st.rerun()  # refit with the new entry
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    st.subheader("Today")
    st.dataframe(d[d.date == str(today)].iloc[::-1], hide_index=True, width="stretch")

with tabs[2]:
    part = st.selectbox("Part", fc.sort_values("rate", ascending=False).index, format_func=label, key="trend")
    dm = F.demand_matrix(h, d)
    row = fc.loc[part]
    c = st.columns(4)
    c[0].metric("Forecast / month", f"{row.rate:.1f}")
    c[1].metric("Typical swing (±)", f"{row.sigma:.1f}")
    c[2].metric("In stock", int(row.stock))
    c[3].metric("Unit price", f"₹{row.price:,.0f}")
    series = dm.loc[part] if part in dm.index else pd.Series(dtype=float)
    st.bar_chart(pd.DataFrame({"Demand (sold + lost)": series}), y_label="units / month")
    st.caption("Blank months are ones where demand couldn't be seen (no stock at all, or COVID lockdown).")

with tabs[3]:
    td = d[d.date == str(today)]
    lost = td[td.kind == "lost"]
    urgent = orders[(orders.stock > 0) & (orders.days_left <= 7)]
    lines = [f"*Parts report · {today:%d %b %Y}*",
             f"Lost sales today: {int(lost.qty.sum())}" + "".join(f"\n  - {r.qty} × {label(r.part)}" for r in lost.itertuples()),
             f"Sold today (logged): {int(td[td.kind == 'sale'].qty.sum())}",
             f"Order list: {len(orders)} lines, ₹{orders.order_value.sum():,.0f}",
             f"Running out within 7 days: {len(urgent)}" + "".join(
                 f"\n  - {label(p)} (stock {int(r.stock)})" for p, r in urgent.head(10).iterrows())]
    st.code("\n".join(lines), language=None)
    st.caption("Copy and paste into WhatsApp.")

with tabs[4]:
    dead = F.dead_stock(h)
    st.metric("Money stuck in parts that haven't sold in 12 months", f"₹{dead.value.sum():,.0f}", f"{len(dead)} parts",
              delta_color="off")
    st.dataframe(dead.reset_index(), hide_index=True, width="stretch")

with tabs[5]:
    st.write("Upload one or more **Month Wise Stock Report (Detailed)** exports. Re-uploading a month replaces it.")
    files = st.file_uploader("HiRise exports", type=["xlsx", "csv"], accept_multiple_files=True)
    if files and st.button("Add to history", type="primary"):
        new = pd.concat([F.read_export(f, f.name) for f in files])
        months = store.add_export(new)
        h2 = store.history()
        after = F.forecast(h2, d)
        before = F.forecast(h2[~h2.month.isin(months)], d)
        diff = after[["desc", "rate"]].join(before.rate.rename("before")).fillna(0)
        diff["change"] = diff.rate - diff.before
        st.session_state.learned = (months, diff.reindex(diff.change.abs().sort_values(ascending=False).index).head(15))
        st.cache_data.clear()
    if "learned" in st.session_state:
        months, diff = st.session_state.learned
        st.success(f"Added {', '.join(months)}. The model refit. Biggest changes in its forecast:")
        st.dataframe(diff.reset_index()[["part", "desc", "before", "rate", "change"]].round(2), hide_index=True,
                     width="stretch", column_config={"before": "Before / month", "rate": "Now / month"})

with tabs[6]:
    st.write("Replays the last 6 months: each month, forecast using only what was known then, "
             "and compare with what actually happened next.")
    if st.button("Run backtest"):
        with st.spinner("Replaying…"):
            r = F.backtest(h, lead_days=s["lead_days"], review_days=s["review_days"], z=s["z"])
        c = st.columns(3)
        c[0].metric("Avg error, this model", r["mae"]["model"])
        c[1].metric("Avg error, 'same as last month'", r["mae"]["last_month"])
        c[2].metric("Avg error, 6-month average", r["mae"]["avg_6m"])
        st.metric("Stockouts of fast movers (≥1/month) flagged a month ahead",
                  f"{r['fast_flagged']} of {r['fast_stockouts']}")
        st.caption(f"Months tested: {', '.join(r['months'])}. All stockouts incl. slow parts: "
                   f"{r['flagged']} of {r['stockouts']} flagged (a slow part selling its one unit is not predictable).")
