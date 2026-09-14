import json
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl


ROOT = Path(__file__).resolve().parent
SOURCE_HTML = ROOT / "index_v34.html"
OUTPUT_HTML = ROOT / "index_v35.html"
SOURCE_XLSX = Path(r"C:\Users\邵新博\Desktop\品牌调研数据汇总表格.xlsx")
MONTHS = ["202604", "202605", "202606", "202607", "202608"]

FIELD_SOURCES = {
    "竞品ASIN": "竞品ASIN",
    "父ASIN": "父ASIN",
    "品牌名": "品牌名",
    "品类": "类目",
    "小类": "小类",
    "风格": "场合风格",
    "面料": "材质大类",
    "是否衬衫": "是否衬衫",
    "袖子类型": "袖长",
    "领型": "领型",
    "版型": "版型",
    "弹力等级": "弹力等级",
    "克重等级": "克重等级",
    "闭合方式": "闭合方式",
    "衣长": "衣长",
    "适用季节": "适用季节",
    "属性状态": "属性状态",
    "卖家名称": "卖家名称",
    "属性1": "属性1",
    "属性2": "属性2",
    "标题": "标题",
    "Buybox价格": "Buybox价格",
    "评分": "评分",
    "父体Rating数": "父体Rating数",
    "大类排名": "大类排名",
    "小类排名": "小类排名",
    "变体数": "变体数",
    "上架日期": "上架日期",
    "数据时间": "月份",
    "抓取时间": "抓取时间",
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
    sheet = workbook["品牌汇总"]
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
        sales = {}
        for key in MONTHS:
            value = values[positions[f"父体销量{key}"]]
            if value not in (None, ""):
                sales[key] = value
        item.update({"链接": "", "sales": sales, "_dataMonth": month, "_monthsOnList": 0, "_isNew": False})
        data.append(item)
    workbook.close()
    return {"sourceName": SOURCE_XLSX.name, "months": MONTHS, "data": data}


def main():
    html = SOURCE_HTML.read_text(encoding="utf-8")
    payload_data = build_payload()
    payload = json.dumps(payload_data, ensure_ascii=False, separators=(",", ":"), default=text)
    html, count = re.subn(
        r"/\*__EMBEDDED_BSR_START__\*/.*?/\*__EMBEDDED_BSR_END__\*/",
        f"/*__EMBEDDED_BSR_START__*/{payload}/*__EMBEDDED_BSR_END__*/",
        html,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("未找到内置数据标记")

    html = html.replace(
        '<tr><td><strong>v34</strong></td>',
        '<tr><td><strong>v35</strong></td><td>2026-09-14</td><td>内置品牌调研表 2026-04 至 2026-08 的 16,860 条原始记录，打开原网址即可查看 8 月数据。</td><td>新数据载入后统一刷新总览、月度对比、排名变化、属性与明细的月份状态；图表继续按“月份＋父ASIN”去重。</td><td><span class="tag tag-green">正式发布</span></td></tr>\n      <tr><td><strong>v34</strong></td>',
        1,
    )
    html = html.replace('<span class="tag tag-blue">本地待验收</span></td></tr>', '<span class="tag tag-green">已发布</span></td></tr>', 1)
    v35_patch = r'''
// ========== V35: EMBEDDED AUGUST DATA STATE SYNC ==========
// New datasets must replace every versioned month selection, not only the visible native selects.
function v35ResetDataViewState(){
  const latest=ALL_MONTHS.at(-1)||'',previous=ALL_MONTHS.at(-2)||'';
  smartState={months:[latest].filter(Boolean),subcats:[],brands:[]};
  compSmartState={months:[latest].filter(Boolean),subcats:[],brands:[]};
  v19State.compareMonths=ALL_MONTHS.slice();v19State.changeMonths=ALL_MONTHS.slice();v19State.changePair=previous&&latest?previous+'|'+latest:'';
  v17AttrMonthState=ALL_MONTHS.slice();
  Object.keys(v33TrendState).forEach(key=>v33TrendState[key]=[]);
  ['fMonth','fCompMonth','fAttrMonth','fDetailMonth','overviewTop100Month'].forEach(id=>{const el=document.getElementById(id);if(el)el.value=monthKeyToLabel(latest)});
  const pairs=[['fBaseMonth',latest],['fCompareMonth',previous],['fChgBaseMonth',latest],['fChgCompareMonth',previous]];
  pairs.forEach(([id,month])=>{const el=document.getElementById(id);if(el)el.value=monthKeyToLabel(month)});
}
const v35BaseRebuildFilterOptions=rebuildFilterOptions;
rebuildFilterOptions=function(){v35ResetDataViewState();const result=v35BaseRebuildFilterOptions();v35ResetDataViewState();return result};

'''
    marker = "// ========== INIT =========="
    if marker not in html:
        raise RuntimeError("未找到初始化标记")
    html = html.replace(marker, v35_patch + marker, 1)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"generated {OUTPUT_HTML.name}: {len(payload_data['data'])} rows")


if __name__ == "__main__":
    main()
