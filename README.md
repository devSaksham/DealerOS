# DealerOS

A dashboard for a Honda two-wheeler dealership. One login, a role per person (admin, parts, sales, service), and a module per department. **Parts** is the first module: it predicts demand for every part from HiRise stock reports and tells the parts manager what to order this week, before the shelf runs empty.

## Parts module
- **Order list:** what to order this week. It covers **regular parts**, meaning parts sold in at least N of 12 months; N is a setting and the screen shows how many parts each N gives. Other parts are ordered only when a customer asked for them and we didn't have them. Rows are sorted by how soon each part runs out.
- **Counter log (voice):** say what happened in English, Hinglish or Hindi, e.g. *"ग्राहक को दो ब्रेक शू चाहिए थे, हमारे पास नहीं थे"*. It finds the matching parts, fills in the quantity, and works out whether it was a lost sale, a sale, or stock received. Lost sales are added back into demand.
- **Daily report:** generate it in any of the three languages, copy it to WhatsApp, or email it to the recipients the admin sets. To send it on a schedule, run `python -m core.report --send` from Windows Task Scheduler.
- **Also:** part trend (festive months marked), dead stock, HiRise upload (shows what the model learned), and an accuracy backtest.
- **Languages:** English, हिन्दी and Hinglish. Switch in the sidebar, including on the sign-in page.

## The model
It is a statistical forecast, not a trained ML model. It predicts **units per month for each part**, for the month the order will arrive, and turns that into an order quantity: enough to last until the next delivery, plus safety stock.

1. **Calendar factor (whole dealership):** a log-linear fit on the total monthly demand of regular parts, with three terms:
   - annual growth;
   - a **festive flag** (1 for any month touched by Dhanteras to Diwali; the dates are in `core/forecast.py`);
   - month-of-year seasonality.

   Each term switches on only with enough history: growth and seasonality need 24 months, the festive effect needs 2 festive months. The dealership's opening ramp-up is left out of the fit.
2. **Per part:** TSB (Teunter–Syntetos–Babai) on the part's demand with the calendar factor divided out. TSB is built for spare parts that sell in bursts. It updates every month, so parts that stop selling fade out and parts that pick up rise.

Months where demand couldn't be seen (no stock at all, or the COVID lockdown) are skipped rather than counted as zero. Only the latest unbroken run of exported months is used.

**Backtest on the real 2018–20 data**, replaying 6 months one month ahead:
- Error on total demand: 16%.
- Error per part: 81%. A part selling 2 a month sells 0, 4, 1, 3…, so any method scores badly here. A 6-month average scores 82% and "same as last month" 93%.
- Of the regular-part stockouts on parts that started the month with stock, 57 of 106 were flagged a month ahead.
- The calendar terms are still off on this data: 15 usable months and 1 festive month. They switch on with the 2024–26 export.

**To see it learn in the demo:** upload `sample_upload/hirise_2026-09.csv` on the Upload HiRise tab.

## Run
```
pip install -r requirements.txt
streamlit run app.py
```
- **Data:** stored in `data/`, which git ignores. On first run it is seeded from `demo_data/`, a synthetic copy with part numbers, quantities, prices and dates scrambled, made by `make_demo.py`.
- **Demo logins:** `admin`, `parts`, `sales` and `service`, all with password `demo`. Change them from the Users page.
- **Demo banner:** set `DEALEROS_DEMO=1` to show the demo logins on the sign-in page.
- **Logic checks:** `python core/forecast.py [export.csv]`, which also runs the backtest when given an export, and `python -m core.i18n`, which checks every UI string is translated.

## Email setup
Add these to `.streamlit/secrets.toml` (git ignores it) or to the Streamlit Cloud Secrets. Use a Gmail **app password**, not the account password:
```
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "465"
SMTP_USER = "you@gmail.com"
SMTP_PASSWORD = "<app password>"
```
The admin adds recipients on the Users page. Email is off in the public demo.

## Add a department
Write `modules/<name>.py` and add one line to `MODULES` in `app.py` with the roles that can see it.
