import json
import re
from collections import Counter
from pathlib import Path


html = Path(__file__).with_name("index_v37.html").read_text(encoding="utf-8")
match = re.search(r"/\*__EMBEDDED_BSR_START__\*/(.*?)/\*__EMBEDDED_BSR_END__\*/", html, re.S)
assert match, "embedded payload missing"
payload = json.loads(match.group(1))
rows = payload["data"]
expected = {"202604": 136, "202605": 127, "202606": 126, "202607": 120, "202608": 122}

assert payload["sourceName"].endswith("· BSR榜单汇总")
assert payload["months"] == list(expected)
assert len(rows) == 983
assert all(key not in rows[0] for key in ("卖家国家", "卖家类型", "图案"))

unique = {}
for row in rows:
    unique.setdefault((row["_dataMonth"], row["父ASIN"] or row["竞品ASIN"]), row)
assert dict(Counter(month for month, _ in unique)) == expected
assert len(rows) - len(unique) == 352
august_sales = sum(0 if str(row["sales"].get("202608", "")).strip() == "92" else float(row["sales"].get("202608", 0) or 0) for (month, _), row in unique.items() if month == "202608")
assert august_sales == 1035499
assert "<strong>v37</strong>" in html
print(f"OK: {len(rows)} BSR rows, {len(unique)} monthly parents, August sales {august_sales:,.0f}")
