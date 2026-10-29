# DealerOS

A dashboard for a Honda two-wheeler dealership. One login, a role per person (admin, parts, sales, service), and a module per department. **Parts** is the first module: it predicts demand for every part from HiRise stock reports and tells the parts manager what to order this week, before the shelf runs empty.

## Parts module
- **Order list:** what to order, sorted by how soon each part runs out. It works out the quantity from the forecast, Honda's lead time, how often you order, and a safety buffer you choose.
- **Counter log (voice):** say what happened, e.g. *"customer wanted 2 brake shoes, we didn't have them"*, using Wispr Flow or by typing. It finds the matching parts, fills in the quantity, and spots that it was a lost sale. Lost sales are added back into demand. Without them, sales records show zero for exactly the parts you keep running out of.
- **Part trend, daily report** (copy and paste into WhatsApp), **dead stock**, **HiRise upload**, and an **accuracy** backtest.

## The model
TSB (Teunter–Syntetos–Babai), a forecasting method made for spare parts that sell in bursts with many zero months. It tracks two numbers for each part: how much sells when it sells, and how often a month has any sales at all. Both update with every new month, so a part that stops selling fades out and a part that picks up rises. Each upload of a HiRise export refits the whole model, and the Upload tab shows which forecasts moved.

Months where demand couldn't be seen (no stock at all, or the COVID lockdown) are skipped rather than counted as zero.

Backtest on the real dealership data (2018–20, replaying 6 months one month ahead):
- Average error is 13% lower than "same as last month".
- It flagged 62 of 78 stockouts of fast-moving parts a month before they happened.

## Run
```
pip install -r requirements.txt
streamlit run app.py
```
- **Data:** stored in `data/`, which git ignores. On first run it is seeded from `demo_data/`, a synthetic copy with part numbers, quantities, prices and dates scrambled, made by `make_demo.py`.
- **Demo logins:** `admin`, `parts`, `sales` and `service`, all with password `demo`. Change them from the Users page.
- **Demo banner:** set `DEALEROS_DEMO=1` to show the demo logins on the sign-in page.
- **Logic checks:** `python core/forecast.py [export.csv]`. Pass an export file to also run the backtest on it.

## Add a department
Write `modules/<name>.py` and add one line to `MODULES` in `app.py` with the roles that can see it.
