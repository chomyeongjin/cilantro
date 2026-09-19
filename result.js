/* ==========================================================================
   Cilantro — result.js
   Renders the 3 recommendation cards from what recommend.js stored after
   submitting the survey. No network call here — see api.js for the
   /api/recommendations contract and how the two pages hand off data.
   ========================================================================== */

// Must match the key recommend.js writes to.
const RESULTS_KEY = "cilantro:recommendations";

// Same "type" ids as products.js' OPTIONS.type — the response only carries
// an id, so the icon is looked up locally rather than sent over the wire.
const PILL_IMAGE = {
  omega3: "images/pills/pill1_1.png",
  "vitamin-b": "images/pills/pill1_2.png",
  "vitamin-c": "images/pills/pill1_3.png",
  magnesium: "images/pills/pill1_4.png",
  probiotics: "images/pills/pill1_5.png",
  lutein: "images/pills/pill1_6.png"
};
const FALLBACK_PILL_IMAGE = "images/pill_sample.png";

const gridEl = document.getElementById("result-grid");

function timingDotPercent(text) {
  if (/아침|오전|기상|공복/.test(text)) return 15;
  if (/밤|저녁|취침|잠들기|잠자기/.test(text)) return 85;
  return 50;
}

function renderCards(items) {
  gridEl.innerHTML = "";

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "result-card";

    const top = document.createElement("div");
    top.className = "result-card-top";
    const img = document.createElement("img");
    img.src = PILL_IMAGE[item.id] || FALLBACK_PILL_IMAGE;
    img.alt = item.name;
    top.appendChild(img);
    card.appendChild(top);

    const body = document.createElement("div");
    body.className = "result-card-body";

    const name = document.createElement("h2");
    name.className = "result-name";
    name.textContent = item.name;
    body.appendChild(name);

    const timing = document.createElement("div");
    timing.className = "result-timing";
    const timingRow = document.createElement("div");
    timingRow.className = "result-timing-row";
    const timingText = document.createElement("span");
    timingText.textContent = item.timing;
    timingRow.appendChild(timingText);
    timing.appendChild(timingRow);
    const track = document.createElement("div");
    track.className = "timing-track";
    const dot = document.createElement("span");
    dot.className = "timing-dot";
    dot.style.left = timingDotPercent(item.timing) + "%";
    track.appendChild(dot);
    timing.appendChild(track);
    body.appendChild(timing);

    const desc = document.createElement("p");
    desc.className = "result-desc";
    desc.textContent = item.description;
    body.appendChild(desc);

    const link = document.createElement("a");
    link.className = "result-link";
    link.href = item.link;
    link.textContent = "제품 보러 가기";
    body.appendChild(link);

    card.appendChild(body);
    gridEl.appendChild(card);
  });
}

function load() {
  let items = null;
  try {
    items = JSON.parse(sessionStorage.getItem(RESULTS_KEY));
  } catch (err) {
    items = null;
  }

  if (!Array.isArray(items) || !items.length) {
    gridEl.innerHTML = "";
    const el = document.createElement("div");
    el.className = "state-message";
    el.textContent = "아직 추천받은 영양제가 없어요. 설문을 먼저 진행해주세요.";
    const link = document.createElement("a");
    link.href = "recommend.html";
    link.className = "state-retry";
    link.textContent = "설문하러 가기";
    el.appendChild(document.createElement("br"));
    el.appendChild(link);
    gridEl.appendChild(el);
    return;
  }

  renderCards(items);
}

initBackLink("recommend.html");
load();
