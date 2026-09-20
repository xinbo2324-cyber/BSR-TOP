import json
import re
from collections import Counter
from pathlib import Path


html = Path("index_v40.html").read_text(encoding="utf-8")
payload = json.loads(re.search(r"/\*__EMBEDDED_BSR_START__\*/(.*?)/\*__EMBEDDED_BSR_END__\*/", html, re.S).group(1))
data = payload["data"]
assert data and all(row["品类"] for row in data)
assert Counter(row["_dataMonth"] for row in data) == {"202604": 197, "202605": 198, "202606": 199, "202607": 196, "202608": 193}
assert payload["sourceName"].endswith("· BSR榜单汇总") and "<strong>v40</strong>" in html
print(f"payload OK: {len(data)} rows")
