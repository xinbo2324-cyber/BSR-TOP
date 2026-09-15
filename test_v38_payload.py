import json
import re
from collections import Counter
from pathlib import Path


html = Path("index_v38.html").read_text(encoding="utf-8")
match = re.search(r"/\*__EMBEDDED_BSR_START__\*/(.*?)/\*__EMBEDDED_BSR_END__\*/", html, re.S)
assert match, "missing embedded payload"
payload = json.loads(match.group(1))
data = payload["data"]
months = Counter(row["_dataMonth"] for row in data)
assert payload["sourceName"].endswith("· BSR榜单汇总")
assert data and all(month in payload["months"] for month in months)
assert "202608" in months
assert "<strong>v38</strong>" in html
print(f"payload OK: {len(data)} rows; months={dict(sorted(months.items()))}")
