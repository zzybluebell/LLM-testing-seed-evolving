You are preparing an investor update for Bluebell SaaS Pte Ltd. Input: data/financials.xlsx, sheet "raw", 36 monthly rows with columns month, mrr, new_customers, churned_customers, cogs, sales_marketing_spend, headcount. We started the period with 120 active customers.

Step 1 — Compute in Python and verify:
- active customers per month = previous active + new_customers − churned_customers (starting from 120)
- gross margin per month = (mrr − cogs) / mrr
- monthly churn = churned_customers / previous month's active customers
- CAC (trailing 12 months) = sum of sales_marketing_spend over the last 12 months / sum of new_customers over the last 12 months
- ARPA = last month's mrr / last month's active customers
- LTV = ARPA × average gross margin (last 12 months) / average monthly churn (last 12 months)
- CAC payback months = CAC / (ARPA × average gross margin over the last 12 months)

Step 2 — Build out/model.xlsx with openpyxl. Sheet "raw": the input data. Sheet "unit_economics": the metrics above as live Excel formulas referencing "raw" (no pasted numbers). Sheet "dcf": an assumptions block (revenue year 0 = sum of the last 12 months of mrr; growth 25%, 21%, 17%, 13%, 10% for years 1–5; FCF margin 15%, 17.5%, 20%, 22.5%, 25%; discount rate 12%; initial investment −5,000,000 at year 0), the 5-year FCF line, and NPV and IRR as Excel formulas (no terminal value). Sheet "loan": principal 2,000,000 at 7% annual, 60 equal monthly payments, a full amortization table, and total interest as a formula.

Step 3 — Render two charts with matplotlib to out/charts/: mrr.png (MRR by month) and customers.png (new vs churned per month).

Step 4 — Build out/investor_update.pptx with python-pptx, 8–12 slides in this order: title; MRR trend (insert mrr.png); gross margin & cost structure; customer growth (insert customers.png); unit economics table with CAC, LTV, LTV/CAC, CAC payback months and ARPA (two decimals); use of funds; appendix listing every assumption.

Step 5 — Re-open both files, check that every number on the slides matches model.xlsx, and print a checklist of what you verified.

Step 6 — Also attached: data/last_board_deck_slide7.png, a screenshot of slide 7 from last quarter's board deck. Compare its numbers with what you computed; if any conflict, state the conflict and the corrected value on the appendix slide.

Step 7 — Export each slide of out/investor_update.pptx to PNG (LibreOffice headless if available, otherwise render with python-pptx + Pillow), inspect the images for overlapping text, cut-off charts or empty placeholders, fix any issue and re-export.

Do not ask questions; make reasonable assumptions and state them on the appendix slide.
