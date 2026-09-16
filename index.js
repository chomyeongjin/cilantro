/* ==========================================================================
   Cilantro — index.js
   Fetches the trending list from the backend and renders the scattered
   layout + What/Why/How popup. No mock data — everything comes from
   Api.getTrending().

   Layout note: items sit in 7 pre-checked, non-overlapping fixed-size
   slots (width AND height fixed, image contained inside) ordered by rank
   so slot 1 is largest. If the backend returns fewer than 7 items, the
   remaining slots are simply unused.
   ========================================================================== */

const SLOTS = [
  { left: 40, top: 130, width: 210, height: 260 },
  { left: 300, top: 130, width: 170, height: 210 },
  { left: 520, top: 60, width: 150, height: 190 },
  { left: 720, top: 130, width: 150, height: 190 },
  { left: 300, top: 380, width: 150, height: 190 },
  { left: 520, top: 300, width: 130, height: 170 },
  { left: 720, top: 360, width: 120, height: 150 }
];

const scatterEl = document.getElementById("scatter");
const overlayEl = document.getElementById("overlay");
const popupEl = document.getElementById("popup");

const popupNameEl = document.getElementById("popup-name");
const popupWhatEl = document.getElementById("popup-what");
const popupWhyEl = document.getElementById("popup-why");
const popupHowTextEl = document.getElementById("popup-how-text");
const popupChartEl = document.getElementById("popup-chart");
const popupCloseEl = document.getElementById("popup-close");
let popupTrigger = null;

function renderItems(items) {
  scatterEl.innerHTML = "";

  items.slice(0, SLOTS.length).forEach((item, index) => {
    const slot = SLOTS[index];
    const btn = document.createElement("button");
    btn.className = "item";
    btn.style.left = slot.left + "px";
    btn.style.top = slot.top + "px";
    btn.style.width = slot.width + "px";
    btn.style.height = slot.height + "px";
    btn.setAttribute("aria-label", item.name);

    const numberEl = document.createElement("span");
    numberEl.className = "item-number";
    numberEl.textContent = (item.rank || index + 1) + ".";
    btn.appendChild(numberEl);

    const imageBox = document.createElement("div");
    imageBox.className = "item-image-box";
    const img = document.createElement("img");
    img.className = "item-img";
    img.src = item.image;
    img.alt = item.name;
    imageBox.appendChild(img);
    btn.appendChild(imageBox);

    btn.addEventListener("click", () => openPopup(item, btn));
    scatterEl.appendChild(btn);
  });
}

function escapeChartText(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
}

function chartValue(value) {
  return Number.isFinite(value) && value >= 0 && value <= 100;
}

function buildChart(data) {
  if (!Array.isArray(data) || !data.some(d => chartValue(d.value))) {
    return '<p>표시할 검색 강도 데이터가 없습니다.</p>';
  }
  const x = i => 30 + (data.length === 1 ? 135 : 270 * i / (data.length - 1));
  const y = value => 132 - value * 1.1;
  let penDown = false;
  const path = [];
  const dots = [];
  data.forEach((point, i) => {
    if (!chartValue(point.value)) { penDown = false; return; }
    path.push(`${penDown ? 'L' : 'M'} ${x(i).toFixed(1)} ${y(point.value).toFixed(1)}`);
    penDown = true;
    // Only isolated observations need dots; the rest form a clean line.
    if (!chartValue(data[i - 1]?.value) && !chartValue(data[i + 1]?.value)) {
      dots.push(`<circle class="chart-dot" cx="${x(i).toFixed(1)}" cy="${y(point.value).toFixed(1)}" r="2"><title>${escapeChartText(point.label)} · ${point.value.toFixed(1)}</title></circle>`);
    }
  });
  const indices = [...new Set([0, Math.floor((data.length - 1) / 2), data.length - 1])];
  const labels = indices.map(i => `<text class="chart-label" x="${x(i).toFixed(1)}" y="154" text-anchor="${i === 0 ? 'start' : i === data.length - 1 ? 'end' : 'middle'}">${escapeChartText(data[i].label)}</text>`).join('');
  return `<svg viewBox="0 0 330 164" role="img" aria-label="날짜별 상대 검색 강도 선 그래프. 0부터 100까지, 누락된 날짜는 선을 끊어 표시합니다.">
    <text class="chart-label" x="30" y="10">상대 검색 강도</text>
    ${[0, 50, 100].map(v => `<line class="chart-axis" x1="30" y1="${y(v)}" x2="300" y2="${y(v)}"></line><text class="chart-label" x="24" y="${y(v) + 3}" text-anchor="end">${v}</text>`).join('')}
    <path class="chart-line" d="${path.join(' ')}"></path>${dots.join('')}
    <line id="chart-cursor" class="chart-cursor" x1="300" x2="300" y1="22" y2="132"></line>
    <circle id="chart-selected" class="chart-dot" cx="300" cy="132" r="3"></circle>
    ${labels}</svg>
    <p id="chart-reading" class="chart-reading" aria-live="polite"></p>
    <input id="chart-date" type="range" min="0" max="${data.length - 1}" value="${data.length - 1}" step="1" aria-label="날짜별 상대 검색 강도 탐색">
    <p class="chart-hint">날짜를 움직여 강도를 확인하세요. 누락된 구간은 선이 끊깁니다.</p>`;
}

function wireChart(data) {
  const slider = document.getElementById('chart-date');
  if (!slider) return;
  const update = () => {
    const index = Number(slider.value);
    const point = data[index];
    const reading = `${point.label} · ${chartValue(point.value) ? point.value.toFixed(1) + ' / 100' : '데이터 없음'}`;
    document.getElementById('chart-reading').textContent = reading;
    slider.setAttribute('aria-valuetext', reading);
    const x = 30 + (data.length === 1 ? 135 : 270 * index / (data.length - 1));
    const cursor = document.getElementById('chart-cursor');
    cursor.setAttribute('x1', x);
    cursor.setAttribute('x2', x);
    const selected = document.getElementById('chart-selected');
    selected.setAttribute('cx', x);
    selected.setAttribute('cy', chartValue(point.value) ? 132 - point.value * 1.1 : 132);
    selected.style.display = chartValue(point.value) ? '' : 'none';
  };
  slider.addEventListener('input', update);
  update();
}

function sourceLink(url, title) {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) return null;
    const link = document.createElement('a');
    link.href = parsed.href;
    link.textContent = title;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    return link;
  } catch { return null; }
}

function openPopup(item, triggerEl) {
  popupTrigger = triggerEl;
  popupNameEl.textContent = item.name;
  popupWhatEl.textContent = item.what;
  const whatSourceEl = document.getElementById('popup-what-source');
  whatSourceEl.replaceChildren();
  if (item.whatSource) {
    const link = sourceLink(item.whatSource.url, item.whatSource.title + ' ↗');
    if (link) whatSourceEl.append(link);
  }
  popupWhyEl.textContent = item.why;
  const newsEl = document.getElementById('popup-news');
  newsEl.replaceChildren();
  (item.whySources || []).forEach(source => {
    const link = sourceLink(source.url, source.title);
    if (!link) return;
    const li = document.createElement('li');
    const date = document.createElement('span');
    date.className = 'news-date';
    date.textContent = `${source.publishedAt} · ${source.publisher}`;
    li.append(link, date);
    newsEl.append(li);
  });
  document.getElementById('popup-interest').textContent = Number.isFinite(item.interestIndex)
    ? `최근 7일 평균 ${item.interestIndex.toFixed(1)} / 100` : '최근 7일 평균 데이터 부족';
  popupHowTextEl.textContent = item.how && item.how.summary;
  popupChartEl.innerHTML = buildChart(item.how?.chart);
  wireChart(item.how?.chart);

  overlayEl.hidden = false;
  popupEl.hidden = false;
  positionPopup(triggerEl);
  document.querySelector('main').inert = true;
  document.getElementById('sidebar').inert = true;
  document.body.classList.add('popup-open');
  popupCloseEl.focus();
}

function positionPopup(triggerEl) {
  const rect = triggerEl.getBoundingClientRect();
  const popupWidth = popupEl.offsetWidth || 320;
  const popupHeight = popupEl.offsetHeight || 320;
  const margin = 12;

  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;

  let left = centerX - popupWidth / 2;
  let top = centerY - popupHeight / 2;

  if (left + popupWidth > window.innerWidth - margin) {
    left = window.innerWidth - popupWidth - margin;
  }
  if (left < margin) left = margin;

  if (top + popupHeight > window.innerHeight - margin) {
    top = window.innerHeight - popupHeight - margin;
  }
  if (top < margin) top = margin;

  popupEl.style.left = left + "px";
  popupEl.style.top = top + "px";
}

function closePopup() {
  if (popupEl.hidden) return;
  overlayEl.hidden = true;
  popupEl.hidden = true;
  document.querySelector('main').inert = false;
  document.getElementById('sidebar').inert = false;
  document.body.classList.remove('popup-open');
  if (popupTrigger?.isConnected) popupTrigger.focus();
}

overlayEl.addEventListener("click", closePopup);
popupCloseEl.addEventListener("click", closePopup);
document.addEventListener("keydown", (e) => {
  if (popupEl.hidden) return;
  if (e.key === "Escape") closePopup();
  if (e.key === 'Tab') {
    const controls = [...popupEl.querySelectorAll('button, a[href], input:not([disabled])')];
    const first = controls[0], last = controls[controls.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
});

async function load() {
  renderLoading(scatterEl, "트렌드 영양제를 불러오는 중...");
  try {
    const items = await Api.getTrending();
    renderItems(items);
  } catch (err) {
    renderError(scatterEl, "트렌드 영양제를 불러오지 못했습니다.", load);
  }
}

load();
