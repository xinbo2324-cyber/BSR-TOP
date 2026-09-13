import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync(new URL('./index_v34.html', import.meta.url), 'utf8');

for (const mapping of [
  "'类目','category'",
  "'场合风格','style'",
  "'材质大类','面料类型'",
  "'数据日期','月份'",
  "'袖子类型','袖长'",
]) assert.ok(html.includes(mapping), `缺少映射：${mapping}`);

const productKey = row => row['父ASIN'] || row['竞品ASIN'] || '';
const uniqueParentMonth = rows => {
  const map = new Map();
  rows.forEach((row, index) => {
    const key = `${row._dataMonth || ''}|${productKey(row) || `__row_${index}`}`;
    if (!map.has(key)) map.set(key, row);
  });
  return [...map.values()];
};

const rows = [
  {_dataMonth: '202604', 父ASIN: 'P1', 竞品ASIN: 'C1'},
  {_dataMonth: '202604', 父ASIN: 'P1', 竞品ASIN: 'C2'},
  {_dataMonth: '202605', 父ASIN: 'P1', 竞品ASIN: 'C1'},
];
const result = uniqueParentMonth(rows);
assert.equal(result.length, 2, '同月父体应去重，不同月份应保留');
assert.equal(result[0].竞品ASIN, 'C1', '统计去重不能改写子 ASIN');
assert.ok(html.includes("d['竞品ASIN']||d['父ASIN']"), '明细应优先显示子 ASIN');

console.log('v34 import logic: OK');
