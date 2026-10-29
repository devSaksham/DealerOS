---
name: dealeros-research
description: Run a research pass for DealerOS. Study competitors from public material, find spare-parts forecasting research, test promising methods against our data, and update the ledgers. Use when asked to study competitors, find better methods, "reverse engineer" a feature, or improve the model from research.
---

# DealerOS research pass

The point of a pass is to learn what others do, test it on our data, and adopt only what wins. Ledgers live in `research/`.

## 1. Competitors → `research/competitors.md`
- **Sources:** public material only. Product and help pages, pricing, case studies, demo-video transcripts, whitepapers, patents (Google Patents).
- **Tools:** use Firecrawl search and scrape.
- **No decompiling or logging into competitors' products.** Their planning runs on their servers, and their licences forbid it.
- For every fact, record the URL, the date checked, and whether it is a **claim** or something **seen**. Update the feature matrix, then tick off or add to the open questions.

## 2. Research → `research/methods.md`
- Search with `firecrawl_research_search_papers`, using several framings: intermittent demand, spare parts, obsolescence, censored demand / stockouts, inventory KPIs, festive or seasonal effects.
- For each new paper, record its ID, the claim, and the status here.

## 3. Test → `research/experiments.py`
- To add a method, write a function `series -> (monthly rate, sigma)`, where NaN means an unobserved month, and add it to `FORECASTERS`. An ordering policy goes in as a new `policies` entry.
- Run `python research/experiments.py <export>` on the newest data in `data/history.csv`, or on the user's HiRise export folder.
- **The deciding score is fill rate for the same stock value.** Two 2026 papers (arXiv 2601.21844, 2609.13840) show that forecast error alone misleads for spare parts.
- **Adopt a method only if** it is no worse on per-part error, total-demand error, and fill rate for the same stock value. Mark results on fewer than 12 test months as provisional.
- Log the run as a dated table in methods.md. If a method wins, move it into `core/forecast.py`, rerun `python core/forecast.py <export>`, and note the change in the README's model section.

## 4. rea (reverse engineering) is for targets the user owns
`morluto/rea` is registered as an MCP server. Use it on:
- the user's own logged-in HiRise session in the browser (`list_browser_targets`, `capture_browser_scenario`), for example to automate the monthly export. The user logs in themselves, because HiRise has a captcha and an OTP;
- DealerOS itself.

Don't point it at competitors' apps.

## 5. Report back
Give a short summary: what's new, what was tested, what was adopted or rejected and why, and what's still open.
