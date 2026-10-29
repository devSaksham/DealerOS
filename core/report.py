"""Daily parts report: build it in any language and email it.
Same code behind the app's "Send report" button and a scheduled run, e.g. Windows Task Scheduler daily at 7 pm:
    python -m core.report --send
SMTP settings come from environment variables or .streamlit/secrets.toml (never the repo):
    SMTP_HOST=smtp.gmail.com  SMTP_PORT=465  SMTP_USER=you@gmail.com  SMTP_PASSWORD=<Gmail app password>"""
import datetime as dt
import os
import re
import smtplib
import sys
from email.message import EmailMessage

import pandas as pd

from core import forecast as F
from core import store
from core.i18n import t

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def snapshot(s=None):
    """Everything the parts page and the report need, computed once."""
    s = s or store.settings()
    h, d = store.history(), store.daily()
    last = h.month.max()
    # Forecast the month the order will arrive in (that's where festive season matters). If exports are
    # months behind, fall back to the month after the last export instead of extrapolating years ahead.
    arrive = (pd.Timestamp.today() + pd.Timedelta(days=s["lead_days"])).strftime("%Y-%m")
    stale = arrive > F.add_months(last, 3)
    fc = F.forecast(h, d, target=F.add_months(last, 1) if stale else arrive, min_active=s["min_active"],
                    calendar=s["calendar"])
    open_lost = d[(d.kind == "lost") & (d.date.str[:7] > last)].groupby("part").qty.sum()
    orders = F.reorder(fc, s["lead_days"], s["review_days"], s["z"], open_lost)
    return {"h": h, "d": d, "fc": fc, "orders": orders, "open_lost": open_lost, "stale": stale, "last": last}


def build(snap, lang="en", day=None):
    """(subject, body text, order-list CSV) for one day."""
    day = day or dt.date.today()
    fc, d, orders = snap["fc"], snap["d"], snap["orders"]
    name = lambda p: f"{p} · {fc.desc.get(p, '')}"  # noqa: E731
    td = d[d.date == str(day)]
    lost = td[td.kind == "lost"]
    reg = fc[fc.regular]
    empty = reg[reg.stock <= 0].sort_values("rate", ascending=False)
    urgent = orders[(orders.stock > 0) & (orders.days_left <= 7)]
    lines = [t("Parts report", lang) + f" · {day:%d %b %Y}", "",
             t("Lost sales today: {n}", lang, n=int(lost.qty.sum()))]
    lines += [f"  - {r.qty} × {name(r.part)}" for r in lost.itertuples()]
    lines += [t("Sold today (logged): {n}", lang, n=int(td[td.kind == "sale"].qty.sum())),
              t("Order list: {n} lines, ₹{v}", lang, n=len(orders), v=f"{orders.order_value.sum():,.0f}"),
              t("Regular parts out of stock: {n} of {total}", lang, n=len(empty), total=len(reg))]
    lines += [f"  - {name(p)}" for p in empty.index[:10]]
    lines += [t("Running out within 7 days: {n}", lang, n=len(urgent))]
    lines += [f"  - {name(p)} ({t('stock', lang)} {int(r.stock)})" for p, r in urgent.head(10).iterrows()]
    if snap["stale"]:
        lines += ["", t("Note: latest HiRise export is {m}. Upload newer months for a better forecast.", lang, m=snap["last"])]
    csv = orders.reset_index()[["part", "desc", "stock", "rate", "order", "price", "order_value", "why"]] \
        .round(1).to_csv(index=False)
    return t("Parts report", lang) + f" · {day:%d %b %Y}", "\n".join(lines), csv


def _cfg(key):
    if os.environ.get(key):
        return os.environ[key]
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:  # no secrets file
        return None


def email_ready():
    return not store.DEMO and all(_cfg(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def send(to, subject, body, csv):
    if not email_ready():
        raise RuntimeError("Email is not set up (or this is the public demo).")
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, _cfg("SMTP_FROM") or _cfg("SMTP_USER"), ", ".join(to)
    msg.set_content(body)  # UTF-8, so Hindi survives
    msg.add_attachment(csv.encode("utf-8-sig"), maintype="text", subtype="csv",
                       filename=f"order_list_{dt.date.today()}.csv")
    port = int(_cfg("SMTP_PORT") or 465)
    if port == 465:
        server = smtplib.SMTP_SSL(_cfg("SMTP_HOST"), port, timeout=30)
    else:
        server = smtplib.SMTP(_cfg("SMTP_HOST"), port, timeout=30)
        server.starttls()
    with server:
        server.login(_cfg("SMTP_USER"), _cfg("SMTP_PASSWORD"))
        server.send_message(msg)


if __name__ == "__main__":
    s = store.settings()
    subject, body, csv = build(snapshot(s), s["report_lang"])
    print(body)
    if "--send" in sys.argv:
        send(s["report_emails"], subject, body, csv)
        print(f"\nSent to {', '.join(s['report_emails'])}")
