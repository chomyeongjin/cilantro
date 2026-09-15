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

function buildChart(data) {
  const width = 256;
  const height = 90;
  const padLeft = 8;
  const padRight = 8;
  const padTop = 12;
  const padBottom = 16;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const maxVal = Math.max(...data.map((d) => d.value));
  const minVal = 0;

  const points = data.map((d, i) => {
    const x = padLeft + (plotW / (data.length - 1)) * i;
    const y = padTop + plotH - ((d.value - minVal) / (maxVal - minVal)) * plotH;
    return { x, y, ...d };
  });

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  const dots = points
    .map(
      (p) => `<circle class="chart-dot" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="2.5"></circle>`
    )
    .join("");

  const labels = points
    .map(
      (p) =>
        `<text class="chart-label" x="${p.x.toFixed(1)}" y="${height - 2}" text-anchor="middle">${p.label}</text>`
    )
    .join("");

  const lastPoint = points[points.length - 1];
  const growth = Math.round(
    ((lastPoint.value - points[0].value) / points[0].value) * 100
  );

  const valueTag = `<text class="chart-value" x="${lastPoint.x.toFixed(1)}" y="${(lastPoint.y - 8).toFixed(1)}" text-anchor="middle">+${growth}%</text>`;

  return `
    <svg viewBox="0 0 ${width} ${height}">
      <line class="chart-axis" x1="${padLeft}" y1="${padTop + plotH}" x2="${width - padRight}" y2="${padTop + plotH}"></line>
      <path class="chart-line" d="${pathD}"></path>
      ${dots}
      ${labels}
      ${valueTag}
    </svg>
  `;
}

function openPopup(item, triggerEl) {
  popupNameEl.textContent = item.name;
  popupWhatEl.textContent = item.what;
  popupWhyEl.textContent = item.why;
  popupHowTextEl.textContent = item.how && item.how.summary;
  popupChartEl.innerHTML = item.how && item.how.chart ? buildChart(item.how.chart) : "";

  overlayEl.hidden = false;
  popupEl.hidden = false;
  positionPopup(triggerEl);
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
  overlayEl.hidden = true;
  popupEl.hidden = true;
}

overlayEl.addEventListener("click", closePopup);
popupEl.addEventListener("click", closePopup);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closePopup();
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
