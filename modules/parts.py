import datetime as dt
import re

import pandas as pd
import streamlit as st

from core import forecast as F
from core import i18n, report, store

user = st.session_state.user
lang = st.session_state.get("lang", "en")
t = lambda s, **k: i18n.t(s, lang, **k)  # noqa: E731
s = st.session_state.get("settings") or store.settings()  # demo: per visitor, not saved
today = dt.date.today()


def save(new):
    if store.DEMO:
        st.session_state.settings = new
    else:
        store.save_settings(new)
    st.rerun()


@st.cache_data
def compute(stamp_, settings_):
    """Refit on every change to the data files (stamp_ = their modified times) or settings."""
    return report.snapshot(settings_)


stamp = tuple(p.stat().st_mtime if p.exists() else 0 for p in (store.HISTORY, store.DAILY))
snap = compute(stamp, s)
h, d, fc, orders, open_lost = snap["h"], snap["d"], snap["fc"], snap["orders"], snap["open_lost"]
label = lambda p: f"{p} · {fc.desc.get(p, '')}"  # noqa: E731
reg = fc[fc.regular]

st.title("🔧 " + t("Parts"))
st.caption(t("Demand history up to {m} · {n} parts, {r} regular · forecast for {target} · refits whenever data changes",
             m=snap["last"], n=f"{len(fc):,}", r=f"{len(reg):,}", target=fc.attrs["target"]))
empty = int((reg.stock <= 0).sum())
if empty:
    st.warning(t("{n} regular parts are out of stock right now.", n=empty), icon="⚠️")
if snap["stale"]:
    st.info(t("Note: latest HiRise export is {m}. Upload newer months for a better forecast.", m=snap["last"]))

tabs = st.tabs([t(x) for x in ["Order list", "Counter log", "Part trend", "Daily report", "Dead stock",
                               "Upload HiRise", "Accuracy"]])

with tabs[0]:
    c = st.columns(4)
    c[0].metric(t("Lines to order"), f"{len(orders):,}")
    c[1].metric(t("Order value"), f"₹{orders.order_value.sum():,.0f}")
    c[2].metric(t("Out of stock / runs out in 7 days"),
                f"{int((orders.stock <= 0).sum())} / {int(((orders.stock > 0) & (orders.days_left <= 7)).sum())}")
    c[3].metric(t("Lost sales logged (open)"), int(open_lost.sum()))
    with st.expander(t("Ordering settings")):
        lead = st.number_input(t("Days from order to delivery (Honda lead time)"), 1, 90, s["lead_days"])
        review = st.number_input(t("Days between orders"), 1, 60, s["review_days"])
        z = st.select_slider(t("Safety level"), [1.0, 1.28, 1.65, 2.05], s["z"],
                             format_func=lambda v: t({1.0: "Lean (84%)", 1.28: "Normal (90%)",
                                                      1.65: "Safe (95%)", 2.05: "Very safe (98%)"}[v]))
        dm = F.demand_matrix(F.latest_run(h), d)
        counts = {k: int(F.regular_parts(dm, k).regular.sum()) for k in range(1, 13)}
        min_active = st.select_slider(t("A part is 'regular' if it sells in at least this many of 12 months"),
                                      list(range(1, 13)), s["min_active"],
                                      format_func=lambda k: f"{k} → {counts[k]:,} " + t("parts"))
        st.caption(t("Regular parts are kept on the shelf. Others are ordered only when a customer asks."))
        if st.button(t("Save settings")):
            save({**s, "lead_days": lead, "review_days": review, "z": z, "min_active": min_active})
    show = orders.reset_index()[["part", "desc", "why", "stock", "rate", "days_left", "order", "price", "order_value"]]
    show["why"] = show.why.map(t)
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "part": t("Part no."), "desc": t("Description"), "why": t("Why"), "stock": t("In stock"),
        "rate": st.column_config.NumberColumn(t("Sells / month"), format="%.1f"),
        "days_left": st.column_config.NumberColumn(t("Days left"), help=t("At the current sales pace")),
        "order": t("Order qty"), "price": st.column_config.NumberColumn(t("Unit ₹"), format="%.0f"),
        "order_value": st.column_config.NumberColumn(t("Value ₹"), format="%.0f")})
    st.download_button(t("Download order list (CSV)"), show.to_csv(index=False), f"order_{today}.csv")

with tabs[1]:
    st.write(t("Say what happened at the counter. Hold your Wispr key and talk, or type."))
    said = st.text_input(t("Example: customer wanted 2 brake shoes, we didn't have them"), key="said")
    low = said.lower()
    words = [i18n.PART_WORDS.get(w, w) for w in i18n.split_words(low)]
    words = [w.rstrip("s") if len(w) > 3 else w for w in words if len(w) > 2 and not w.isdigit()]
    text = pd.Series(fc.index.str.lower(), index=fc.index) + " " + fc.desc.fillna("").str.lower()
    score = sum(text.str.contains(re.escape(w)).astype(int) for w in words) if words else None
    matches = list(score[score > 0].sort_values(ascending=False).index[:10]) if words else []
    nums = re.findall(r"\b\d{1,3}\b", said) or [i18n.NUMBER_WORDS[w] for w in i18n.split_words(low)
                                                  if w in i18n.NUMBER_WORDS]
    kind_said = i18n.kind_of(said)
    with st.form("log", clear_on_submit=True):
        part = st.selectbox(t("Part"), matches or list(fc.index), format_func=label,
                            help=t("Best matches for what you said come first"))
        cols = st.columns(3)
        qty = cols[0].number_input(t("Qty"), 1, 999, int(nums[0]) if nums else 1)
        kinds = {"lost": t("Lost sale (we didn't have it)"), "sale": t("Sold"), "received": t("Received from Honda")}
        kind = cols[1].radio(t("What happened"), list(kinds), format_func=kinds.get, index=list(kinds).index(kind_said))
        date = cols[2].date_input(t("Date"), today)
        if st.form_submit_button(t("Save"), type="primary"):
            store.add_daily(date, part, qty, kind, said, user["username"])
            st.session_state.flash = t("Saved: {what} · {qty} × {part}", what=kinds[kind], qty=qty, part=label(part))
            del st.session_state["said"]
            st.rerun()  # refit with the new entry
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    st.subheader(t("Today"))
    st.dataframe(d[d.date == str(today)].iloc[::-1], hide_index=True, width="stretch")

with tabs[2]:
    part = st.selectbox(t("Part"), fc.sort_values("rate", ascending=False).index, format_func=label, key="trend")
    dm = F.demand_matrix(F.latest_run(h), d)
    row = fc.loc[part]
    c = st.columns(5)
    c[0].metric(t("Forecast / month"), f"{row.rate:.1f}")
    c[1].metric(t("Typical swing (±)"), f"{row.sigma:.1f}")
    c[2].metric(t("In stock"), int(row.stock))
    c[3].metric(t("Unit price"), f"₹{row.price:,.0f}")
    c[4].metric(t("Regular?"), t("Yes") if row.regular else t("No"), f"{int(row.active)}/12 " + t("months"),
                delta_color="off")
    series = dm.loc[part] if part in dm.index else pd.Series(dtype=float)
    chart = pd.DataFrame({t("Demand (sold + lost)"): series,
                          t("Festive month"): [series.max() if m in F.FESTIVE else None for m in series.index]})
    st.bar_chart(chart, y_label=t("units / month"), stack=False)
    st.caption(t("Blank months are ones where demand couldn't be seen (no stock at all, or COVID lockdown)."))

with tabs[3]:
    rlang = st.radio(t("Report language"), list(i18n.LANGS), format_func=i18n.LANGS.get, horizontal=True,
                     index=list(i18n.LANGS).index(lang))
    if st.button(t("Generate report")) or st.session_state.get("report_key") != (rlang, stamp):
        st.session_state.report, st.session_state.report_key = report.build(snap, rlang), (rlang, stamp)
    subject, body, csv = st.session_state.report
    st.code(body, language=None)
    st.caption(t("Copy and paste into WhatsApp, or send it by email."))
    to = s["report_emails"]
    if not report.email_ready():
        st.info(t("Email is not set up yet. An admin adds SMTP settings and recipients on the Users page."))
    elif not to:
        st.info(t("No recipients yet. An admin adds them on the Users page."))
    elif st.button(t("Send report"), type="primary"):
        try:
            report.send(to, subject, body, csv)
            st.success(t("Sent to {to}", to=", ".join(to)))
        except Exception as e:  # show SMTP errors to the user instead of crashing the page
            st.error(t("Could not send: {err}", err=e))

with tabs[4]:
    dead = F.dead_stock(h)
    st.metric(t("Money stuck in parts that haven't sold in 12 months"), f"₹{dead.value.sum():,.0f}",
              f"{len(dead)} " + t("parts"), delta_color="off")
    st.dataframe(dead.reset_index(), hide_index=True, width="stretch")

with tabs[5]:
    st.write(t("Upload one or more **Month Wise Stock Report (Detailed)** exports. Re-uploading a month replaces it."))
    files = st.file_uploader(t("HiRise exports"), type=["xlsx", "csv"], accept_multiple_files=True)
    if files and st.button(t("Add to history"), type="primary"):
        new = pd.concat([F.read_export(f, f.name) for f in files])
        months = store.add_export(new)
        h2 = store.history()
        after = F.forecast(h2, d, min_active=s["min_active"], calendar=s["calendar"])
        before = F.forecast(h2[~h2.month.isin(months)], d, min_active=s["min_active"], calendar=s["calendar"])
        diff = after[["desc", "rate"]].join(before.rate.rename("before")).fillna(0)
        diff["change"] = diff.rate - diff.before
        st.session_state.learned = (months, diff.reindex(diff.change.abs().sort_values(ascending=False).index).head(15))
        st.cache_data.clear()
    if "learned" in st.session_state:
        months, diff = st.session_state.learned
        st.success(t("Added {months}. The model refit. Biggest changes in its forecast:", months=", ".join(months)))
        st.dataframe(diff.reset_index()[["part", "desc", "before", "rate", "change"]].round(2), hide_index=True,
                     width="stretch", column_config={"before": t("Before / month"), "rate": t("Now / month")})

with tabs[6]:
    cal = fc.attrs["calendar"]
    st.subheader(t("Calendar effects (whole dealership)"))
    c = st.columns(3)
    c[0].metric(t("Annual growth"), f"{cal['annual_growth_pct']:+.1f}%")
    c[1].metric(t("Festive month (Dhanteras–Diwali)"), f"{cal['festive_effect_pct']:+.1f}%")
    c[2].metric(t("Months of history used"), cal["months"])
    st.caption(t("Each effect switches on only with enough history: growth and month-of-year seasonality need "
                 "24 months, the festive effect needs 2 festive months. Until then it stays at 0%."))
    if any(cal["season_pct"].values()):
        st.bar_chart(pd.Series(cal["season_pct"], name="%"), y_label=t("% vs average month"))
    if st.toggle(t("Use calendar effects"), s["calendar"]) != s["calendar"]:
        save({**s, "calendar": not s["calendar"]})
    st.divider()
    st.write(t("Replays the last 6 months: each month, forecast using only what was known then, "
               "and compare with what actually happened next. Scored on regular parts."))
    if st.button(t("Run backtest")):
        with st.spinner(t("Replaying…")):
            r = F.backtest(h, min_active=s["min_active"], lead_days=s["lead_days"], review_days=s["review_days"], z=s["z"])
        names = {"model": t("This model"), "no_calendar": t("Without calendar effects"),
                 "last_month": t("'Same as last month'"), "avg_6m": t("6-month average")}
        st.dataframe(pd.DataFrame({t("Error per part"): r["wape"], t("Error on total demand"): r["total_error"]})
                     .rename(index=names).map(lambda v: f"{v:.0%}"), width="stretch")
        st.metric(t("Regular-part stockouts flagged a month ahead"), f"{r['flagged']} / {r['stockouts']}")
        st.caption(t("Months tested: {m}. Error per part is high for any method: a part selling 2 a month "
                     "sells 0, 4, 1, 3… The order list protects against that with safety stock.",
                     m=", ".join(r["months"])))
