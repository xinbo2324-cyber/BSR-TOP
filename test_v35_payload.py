import json
import re
from collections import Counter
from pathlib import Path


HTML = Path(__file__).with_name("index_v35.html")
EXPECTED_COUNTS = {"202604": 3453, "202605": 3572, "202606": 3176, "202607": 3468, "202608": 2916}


html = HTML.read_text(encoding="utf-8")
match = re.search(r"/\*__EMBEDDED_BSR_START__\*/(.*?)/\*__EMBEDDED_BSR_END__\*/", html, re.S)
assert match, "embedded payload missing"
payload = json.loads(match.group(1))
rows = payload["data"]

assert payload["sourceName"] == "品牌调研数据汇总表格.xlsx"
assert payload["months"] == list(EXPECTED_COUNTS)
assert len(rows) == 16860
assert all(key not in rows[0] for key in ("卖家国家", "卖家类型", "图案"))

unique = {}
for row in rows:
    key = (row["_dataMonth"], row["父ASIN"] or row["竞品ASIN"])
    unique.setdefault(key, row)

counts = Counter(month for month, _ in unique)
assert dict(counts) == EXPECTED_COUNTS, counts
assert len(rows) - len(unique) == 275

august_sales = sum(
    0 if str(row.get("sales", {}).get("202608", "")).strip() == "92" else float(row.get("sales", {}).get("202608", 0) or 0)
    for (month, _), row in unique.items()
    if month == "202608"
)
assert august_sales == 6893952, august_sales
assert "function v35ResetDataViewState()" in html
assert "<strong>v35</strong>" in html
print(f"OK: {len(rows)} rows, {len(unique)} monthly parents, August sales {august_sales:,.0f}")
