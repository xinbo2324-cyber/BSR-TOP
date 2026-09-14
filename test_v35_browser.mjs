const endpoint = 'http://127.0.0.1:9335/json/list';
const dashboard = process.env.DASHBOARD_FILE || 'index_v35.html';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
let page;
for (let i = 0; i < 60; i++) {
  try {
    const pages = await fetch(endpoint).then(response => response.json());
    page = pages.find(item => item.type === 'page' && item.url.includes(dashboard));
    if (page) break;
  } catch {}
  await wait(500);
}
if (!page) throw new Error('Chrome page not found');

const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, {once: true});
  socket.addEventListener('error', reject, {once: true});
});
let id = 0;
const pending = new Map();
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    pending.get(message.id)(message);
    pending.delete(message.id);
  }
});
const send = (method, params = {}) => new Promise(resolve => {
  const requestId = ++id;
  pending.set(requestId, resolve);
  socket.send(JSON.stringify({id: requestId, method, params}));
});
const evaluate = async expression => {
  const response = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (response.result?.exceptionDetails) throw new Error(response.result.exceptionDetails.text);
  return response.result.result.value;
};

let ready = false;
for (let i = 0; i < 80; i++) {
  ready = await evaluate("document.readyState==='complete' && document.getElementById('headerDesc')?.textContent.includes('16860')");
  if (ready) break;
  await wait(500);
}
if (!ready) throw new Error('Dashboard did not finish loading');

const result = await evaluate(`(() => ({
  header: document.getElementById('headerDesc')?.textContent,
  months: ALL_MONTHS,
  selectors: Object.fromEntries(['fMonth','fDetailMonth','fAttrMonth','fBaseMonth','fCompareMonth','fChgBaseMonth','fChgCompareMonth','overviewTop100Month'].map(id => [id, document.getElementById(id)?.value])),
  comparePair: v19Pair('compare'),
  changePair: v19Pair('change'),
  attrMonths: v17SelectedAttrMonths(),
  top100Rows: document.querySelectorAll('#overviewTop10Body tr').length,
  detailRows: document.querySelectorAll('#detailBody tr').length,
  augustRows: ALL_DATA.filter(row => row._dataMonth === '202608').length,
  augustParents: smartUnique(ALL_DATA.filter(row => row._dataMonth === '202608')).length,
  primaryNativeIndex: [...document.getElementById('fSubCategory').options].findIndex(option => option.value === "Women's Button-Down Shirts"),
  primaryV4Index: [...document.querySelectorAll('#v4MenuOverviewSubcats input[data-v4-value]')].findIndex(input => input.dataset.v4Value === "Women's Button-Down Shirts"),
  primaryV4Color: getComputedStyle([...document.querySelectorAll('#v4MenuOverviewSubcats input[data-v4-value]')].find(input => input.dataset.v4Value === "Women's Button-Down Shirts")?.nextElementSibling).color,
  chartCount: Object.keys(charts).length
}))()`);

const expectedLatest = ['fMonth','fDetailMonth','fAttrMonth','fBaseMonth','fChgBaseMonth','overviewTop100Month'];
for (const key of expectedLatest) if (result.selectors[key] !== '2026-08') throw new Error(`${key}=${result.selectors[key]}`);
for (const key of ['fCompareMonth','fChgCompareMonth']) if (result.selectors[key] !== '2026-07') throw new Error(`${key}=${result.selectors[key]}`);
if (result.comparePair.cur !== '202608' || result.comparePair.prev !== '202607') throw new Error('compare pair stale');
if (result.changePair.cur !== '202608' || result.changePair.prev !== '202607') throw new Error('change pair stale');
if (!result.attrMonths.includes('202608')) throw new Error('attribute months missing August');
if (result.augustRows !== 3012 || result.augustParents !== 2916) throw new Error('August row counts mismatch');
if (result.primaryNativeIndex !== 1 || result.primaryV4Index !== 0 || result.primaryV4Color !== 'rgb(220, 38, 38)') throw new Error('primary subcategory pin failed');
if (!result.top100Rows || !result.detailRows || result.chartCount < 10) throw new Error('dashboard content missing');
console.log(JSON.stringify(result, null, 2));
socket.close();
