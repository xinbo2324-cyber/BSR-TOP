import json
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl


ROOT = Path(__file__).resolve().parent
SOURCE_HTML = ROOT / "index_v36.html"
OUTPUT_HTML = ROOT / "index_v37.html"
SOURCE_XLSX = Path(r"C:\Users\邵新博\WorkBuddy\2026-09-04-19-34-12\output\月度品牌调研_汇总_归类版.xlsx")
SHEET_NAME = "BSR榜单汇总"
MONTHS = ["202604", "202605", "202606", "202607", "202608"]
FIELD_SOURCES = {
    "竞品ASIN": "竞品ASIN", "父ASIN": "父ASIN", "品牌名": "品牌名", "品类": "类目", "小类": "小类",
    "风格": "场合风格", "面料": "面料大类", "是否衬衫": "是否衬衫", "袖子类型": "袖长", "领型": "领型",
    "版型": "版型", "弹力等级": "弹性", "克重等级": "克重等级", "闭合方式": "闭合方式", "衣长": "衣长",
    "适用季节": "适用季节", "属性状态": "属性状态", "卖家名称": "卖家名称", "属性1": "属性1", "属性2": "属性2",
    "标题": "标题", "Buybox价格": "Buybox价格", "评分": "评分", "父体Rating数": "父体Rating数", "大类排名": "大类排名",
    "小类排名": "小类排名", "变体数": "变体数", "上架日期": "上架日期", "数据时间": "月份", "抓取时间": "抓取时间",
}


def text(value):
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def data_month(value):
    match = re.search(r"(\d{1,2})", text(value))
    return f"2026{int(match.group(1)):02d}" if match else ""


def build_payload():
    workbook = openpyxl.load_workbook(SOURCE_XLSX, read_only=True, data_only=True)
    sheet = workbook[SHEET_NAME]
    rows = sheet.iter_rows(values_only=True)
    headers = [text(value) for value in next(rows)]
    positions = {name: index for index, name in enumerate(headers)}
    missing = sorted(set(FIELD_SOURCES.values()) - positions.keys())
    if missing:
        raise ValueError(f"缺少必需列: {missing}")
    data = []
    for values in rows:
        item = {target: text(values[positions[source]]) for target, source in FIELD_SOURCES.items()}
        month = data_month(values[positions["月份"]])
        if month not in MONTHS:
            raise ValueError(f"无法识别月份: {values[positions['月份']]}")
        sales = {key: values[positions[f"父体销量{key}"]] for key in MONTHS if values[positions[f"父体销量{key}"]] not in (None, "")}
        item.update({"链接": "", "sales": sales, "_dataMonth": month, "_monthsOnList": 0, "_isNew": False})
        data.append(item)
    workbook.close()
    return {"sourceName": f"{SOURCE_XLSX.name} · {SHEET_NAME}", "months": MONTHS, "data": data}


def main():
    html = SOURCE_HTML.read_text(encoding="utf-8")
    payload_data = build_payload()
    payload = json.dumps(payload_data, ensure_ascii=False, separators=(",", ":"), default=text)
    html, count = re.subn(r"/\*__EMBEDDED_BSR_START__\*/.*?/\*__EMBEDDED_BSR_END__\*/", f"/*__EMBEDDED_BSR_START__*/{payload}/*__EMBEDDED_BSR_END__*/", html, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("未找到内置数据标记")
    html = html.replace(
        '<tr><td><strong>v36</strong></td>',
        '<tr><td><strong>v37</strong></td><td>2026-09-15</td><td>数据源替换为《月度品牌调研_汇总_归类版》的 BSR榜单汇总子表。</td><td>仅内置该子表的 983 条记录，保留 2026-04 至 2026-08 独立快照、父ASIN去重与小类主类目顶置。</td><td><span class="tag tag-green">正式发布</span></td></tr>\n      <tr><td><strong>v36</strong></td>',
        1,
    )
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"generated {OUTPUT_HTML.name}: {len(payload_data['data'])} rows")


if __name__ == "__main__":
    main()
