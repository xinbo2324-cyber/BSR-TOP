import json
import re
from pathlib import Path

import build_v39 as source


ROOT = Path(__file__).resolve().parent
OUTPUT_HTML = ROOT / "index_v40.html"
source.SOURCE_HTML = ROOT / "index_v39.html"
source.SOURCE_XLSX = Path(r"C:\Users\邵新博\Desktop\月度品牌调研_汇总_归类版_卖家精灵补充_全量.xlsx")
source.FIELD_SOURCES = {**source.FIELD_SOURCES, "品类": "大类"}


def main():
    html = source.SOURCE_HTML.read_text(encoding="utf-8")
    payload_data = source.build_payload()
    payload = json.dumps(payload_data, ensure_ascii=False, separators=(",", ":"), default=source.text)
    html, count = re.subn(r"/\*__EMBEDDED_BSR_START__\*/.*?/\*__EMBEDDED_BSR_END__\*/", f"/*__EMBEDDED_BSR_START__*/{payload}/*__EMBEDDED_BSR_END__*/", html, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("未找到内置数据标记")
    html = html.replace(
        '<tr><td><strong>v39</strong></td>',
        f'<tr><td><strong>v40</strong></td><td>2026-09-20</td><td>更新桌面《月度品牌调研_汇总_归类版_卖家精灵补充_全量》的 BSR榜单汇总子表数据。</td><td>仅内置该子表的 {len(payload_data["data"])} 条有效记录；源表“大类”映射为看板品类，保留现有筛选与图表。</td><td><span class="tag tag-green">正式发布</span></td></tr>\n      <tr><td><strong>v39</strong></td>',
        1,
    )
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"generated {OUTPUT_HTML.name}: {len(payload_data['data'])} rows")


if __name__ == "__main__":
    main()
