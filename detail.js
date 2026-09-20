/* ==========================================================================
   Cilantro — detail.js
   Generic single-product detail page, driven entirely by the backend.
   URL: detail.html?id=<productId>  (e.g. now-ultra-omega3)

   Ingredient bubble diagram: the backend returns ingredients pre-sorted by
   pct (share of formula) desc. Circle diameter is scaled from pct so size
   order always matches ratio order. The largest ingredient anchors the
   diagram; the rest are placed radially around it with a simple outward
   collision check so bubbles never overlap regardless of how many
   ingredients (or what their percentages) come back from the API.
   ========================================================================== */

const PILL_IMG = "images/pill_sample.png";

const BUBBLE_COLORS = ["#f3d7de", "#BFD6F6", "#cfcfcf", "#fbe6ec", "#e3ddc9", "#d8e88a"];
const DECORATIVE_DOTS = [
  { cx: 58, cy: 40, size: 7 },
  { cx: 88, cy: 82, size: 6 }
];

const MAX_BUBBLE = 46;
const MIN_BUBBLE = 17;
const PUSH_DISTANCE = 6;
const NEIGHBOUR_SHRINK = 0.82;

// Compact labels for the supplied label claims; the full source text stays in the API.
const EFFECT_KEYWORDS = {
  "혈중 중성지질·혈행 개선에 도움을 줄 수 있음": ["중성지질 개선", "혈행 개선"],
  "혈행·중성지질·눈 건조·기억력 개선에 도움을 줄 수 있음": ["혈행 개선", "중성지질 개선", "눈 건조 개선", "기억력 개선"],
  "혈중 중성지질·혈행 개선, 건조한 눈 개선에 도움을 줄 수 있음": ["중성지질 개선", "혈행 개선", "눈 건조 개선"],
  "어두운 곳에서 시각 적응, 피부·점막의 기능 유지에 필요": ["시각 적응", "피부·점막 유지"],
  "칼슘·인 흡수와 이용, 뼈 형성·유지에 필요": ["칼슘·인 흡수", "뼈 건강"],
  "항산화 작용으로 유해산소로부터 세포 보호에 필요": ["항산화", "세포 보호"]
};

const titleEl = document.getElementById("detail-title");
const gridEl = document.getElementById("detail-grid");
const backLinkEl = document.querySelector(".back-link");

let bubbleData = [];
const bubbleEls = new Map();

function ingredientAmount(fact) {
  if (fact.amountPerServing == null) return "함량 미확인";
  if (fact.unit === "CFU") return `${(fact.amountPerServing / 100000000).toLocaleString()}억 CFU`;
  return `${fact.amountPerServing.toLocaleString()} ${(fact.unit || "").replace("mcg", "μg")}`;
}

function buildLayout() {
  gridEl.innerHTML = `
    <section class="detail-left">
      <div class="detail-head">
        <span class="brand" id="detail-brand"></span>
        <span class="product-name" id="detail-product-name"></span>
      </div>

      <div class="detail-images">
        <img class="detail-bottle" id="detail-bottle" alt="">

        <div class="detail-size">
          <div class="sub-label">size</div>
          <img class="detail-pill" id="detail-pill" src="${PILL_IMG}" alt="actual pill size">
          <span class="example-yellow-pill" id="detail-example-pill" role="img" aria-label="노란 알약 사진 · 크기 예시" hidden></span>
          <div class="size-ruler" id="detail-ruler"></div>
          <div class="size-caption" id="detail-size-caption"></div>
        </div>
      </div>

      <hr class="divider divider-thin">

      <div class="detail-for">
        <div class="sub-label">for</div>
        <ul id="detail-for-list"></ul>
      </div>

      <a class="buy-link" id="detail-buy-link" target="_blank" rel="noopener">go for shopping</a>
    </section>

    <section class="detail-right">
      <div class="ingredient-diagram" id="ingredient-diagram"></div>
      <p id="diagram-note" class="diagram-note"></p>
      <details class="product-details">
        <summary>성분 함량·섭취 정보 보기</summary>
        <p id="detail-example-note" class="product-note" hidden></p>
        <p id="detail-serving"></p>
        <div id="detail-facts"></div>
        <ul id="detail-warnings" class="product-warnings"></ul>
        <div id="detail-matching"></div>
      </details>
    </section>
  `;
}

function renderProduct(product) {
  titleEl.textContent = product.categoryLabel;
  const shortName = product.product.replace(/\s*·\s*\d+\s*(?:캡슐|정)\s*[×xX]\s*\d+\s*개\s*$/, "");
  document.title = `Cilantro — ${product.brand} ${shortName}`;

  if (backLinkEl && product.categoryId) {
    backLinkEl.href = `category.html?id=${encodeURIComponent(product.categoryId)}`;
  }

  document.getElementById("detail-brand").textContent = product.brand;
  document.getElementById("detail-product-name").textContent = shortName;

  const bottle = document.getElementById("detail-bottle");
  bottle.src = product.image;
  bottle.alt = `${product.brand} ${shortName}`;

  const exampleSize = product.analysisStatus === "example" && !product.pillSizeMm;
  const pillWidth = pillWidthFor(exampleSize ? 10 : product.pillSizeMm);
  document.getElementById("detail-example-pill").hidden = !exampleSize;
  document.getElementById("detail-example-pill").style.width = pillWidth + "px";
  if (product.pillImage && product.pillImage.startsWith("/images/")) {
    const photo = document.createElement("img");
    photo.src = product.pillImage;
    photo.alt = "";
    document.getElementById("detail-example-pill").appendChild(photo);
    document.getElementById("detail-example-pill").classList.add("has-photo");
    document.getElementById("detail-pill").src = product.pillImage;
  }
  document.getElementById("detail-pill").style.width = pillWidth + "px";
  document.getElementById("detail-ruler").style.width = pillWidth + "px";
  document.getElementById("detail-size-caption").textContent = product.pillSizeMm
    ? `${product.pillSizeMm}mm`
    : exampleSize ? "1cm (예시)" : "미확인";
  document.getElementById("detail-pill").hidden = !product.pillSizeMm;
  document.getElementById("detail-ruler").hidden = !product.pillSizeMm && !exampleSize;

  const forList = document.getElementById("detail-for-list");
  forList.closest(".detail-for").hidden = !(product.for || []).length;
  (product.for || []).forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    forList.appendChild(li);
  });

  const buyLink = document.getElementById("detail-buy-link");
  buyLink.href = product.buyLink || "#";

  const note = document.getElementById("detail-example-note");
  note.hidden = !product.exampleNote;
  note.textContent = product.exampleNote || "";
  document.getElementById("detail-serving").textContent = product.serving?.value || "";
  const facts = document.getElementById("detail-facts");
  const heading = document.createElement("h2");
  heading.textContent = "1회 섭취량 기준 성분";
  facts.appendChild(heading);
  const list = document.createElement("dl");
  list.className = "ingredient-facts";
  (product.ingredientFacts || []).forEach((fact) => {
    const name = document.createElement("dt");
    name.textContent = fact.name;
    const amount = document.createElement("dd");
    amount.textContent = ingredientAmount(fact);
    list.append(name, amount);
  });
  facts.appendChild(list);
  const warnings = document.getElementById("detail-warnings");
  (product.warnings || []).forEach((warning) => {
    const li = document.createElement("li");
    li.textContent = warning.value;
    warnings.appendChild(li);
  });
  (product.unknowns || []).forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    warnings.appendChild(li);
  });
  const matching = document.getElementById("detail-matching");
  const matchingTitle = document.createElement("h2");
  matchingTitle.textContent = "기대효과·연령 연결 근거";
  matching.appendChild(matchingTitle);
  const matchingNote = document.createElement("p");
  matchingNote.textContent = product.matchingNotice || "연결 근거 미확인";
  matching.appendChild(matchingNote);
  const reviewedMatches = [...(product.effectMatches || []), ...(product.ageMatches || []).slice(0, 1)];
  reviewedMatches.forEach(match => {
    const line = document.createElement("p");
    line.textContent = `${match.basis === "nutrient_function" ? "성분 기능" : "제품 표시"} · ${match.reason} `;
    if (match.sourceUrl?.startsWith("https://")) {
      const source = document.createElement("a");
      source.href = match.sourceUrl;
      source.textContent = "근거 확인";
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      line.appendChild(source);
    }
    matching.appendChild(line);
  });
  (product.selectionCautions || []).forEach(warning => {
    const line = document.createElement("p");
    line.textContent = warning.text;
    matching.appendChild(line);
  });
  if (product.ingredients?.length) {
    renderDiagram(product.ingredients);
    document.getElementById("diagram-note").textContent = "전체 제형 중량 기준 · 작은 원은 가독성을 위해 확대 표시";
  } else {
    const bubbles = (product.ingredientFacts || []).filter(f => !f.partOf).map(f => ({
      id: f.key, name: f.name,
      amount: ingredientAmount(f),
      weight: f.amountMgPerServing ?? 0,
      incomparable: f.amountMgPerServing == null,
      effects: (product.claims || []).filter(c => c.ingredientKeys.includes(f.key)).map(c => c.text),
      sideEffects: []
    })).sort((a, b) => b.weight - a.weight);
    renderDiagram(bubbles);
    document.getElementById("diagram-note").textContent =
      "mg 환산 가능한 성분의 상대 함량을 표시합니다. 작은 원은 확대 표시하며 전체 구성비는 아닙니다. 점선 원은 단위가 달라 크기 비교에서 제외한 성분입니다.";
  }
}

function layoutIngredients(ingredients) {
  const maxPct = Math.max(...ingredients.map(ing => ing.weight ?? ing.pct ?? 0), 0) || 1;

  const placed = [];

  ingredients.forEach((ing, index) => {
    const size = Math.max(
      MIN_BUBBLE,
      Math.min(MAX_BUBBLE, Math.sqrt((ing.weight ?? ing.pct ?? 0) / maxPct) * MAX_BUBBLE)
    );

    let cx, cy;
    if (index === 0) {
      cx = 38;
      cy = 60;
    } else {
      const angleStep = 360 / Math.max(1, ingredients.length - 1);
      const angle = (angleStep * (index - 1) - 90 + (index % 2 === 0 ? 12 : -12)) * (Math.PI / 180);
      let radius = (placed[0].size + size) / 2 + 8;
      let attempts = 0;
      let candidateCx, candidateCy, collides;

      do {
        candidateCx = placed[0].cx + radius * Math.cos(angle);
        candidateCy = placed[0].cy + radius * Math.sin(angle);
        collides = placed.some((p) => {
          const dx = candidateCx - p.cx;
          const dy = candidateCy - p.cy;
          const dist = Math.sqrt(dx * dx + dy * dy);
          return dist < (p.size + size) / 2 + 4;
        });
        if (collides) radius += 6;
        attempts++;
      } while (collides && attempts < 12);

      cx = candidateCx;
      cy = candidateCy;
    }

    cx = Math.max(size / 2, Math.min(100 - size / 2, cx));
    cy = Math.max(size / 2, Math.min(100 - size / 2, cy));

    placed.push({
      id: ing.id,
      name: ing.name,
      amount: ing.amount,
      incomparable: ing.incomparable,
      effects: ing.effects || [],
      sideEffects: ing.sideEffects || [],
      color: BUBBLE_COLORS[index % BUBBLE_COLORS.length],
      cx,
      cy,
      size,
      interactive: true
    });
  });

  return placed;
}

function clampPercent(value, size) {
  return Math.max(0, Math.min(100 - size, value));
}

function applyGeometry(el, cx, cy, size) {
  const left = clampPercent(cx - size / 2, size);
  const top = clampPercent(cy - size / 2, size);
  el.style.left = left + "%";
  el.style.top = top + "%";
  el.style.width = size + "%";
  el.style.height = size + "%";
}

function renderDiagram(ingredients) {
  const diagramEl = document.getElementById("ingredient-diagram");
  diagramEl.innerHTML = "";
  bubbleEls.clear();

  if (!ingredients.length) {
    renderError(diagramEl, "성분 정보를 불러오지 못했습니다.");
    return;
  }

  bubbleData = layoutIngredients(ingredients).concat(
    DECORATIVE_DOTS.map((d) => ({ ...d, interactive: false, color: BUBBLE_COLORS[BUBBLE_COLORS.length - 1] }))
  );

  const halo = document.createElement("div");
  halo.className = "diagram-halo";
  diagramEl.appendChild(halo);

  bubbleData.forEach((data, i) => {
    const id = data.id || `dot-${i}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble" + (data.interactive ? " is-interactive" : "");
    if (data.incomparable) bubble.classList.add("is-incomparable");
    if (data.interactive) bubble.title = `${data.name} ${data.amount}${data.incomparable ? " · 크기 비교 제외" : ""}`;
    applyGeometry(bubble, data.cx, data.cy, data.size);

    const fill = document.createElement("div");
    fill.className = "bubble-fill";
    fill.style.background = data.color;
    bubble.appendChild(fill);

    if (data.interactive) {
      const content = document.createElement("div");
      content.className = "bubble-content";

      const title = document.createElement("div");
      title.className = "bubble-title";
      const name = document.createElement("span");
      name.className = "bubble-name";
      name.textContent = data.name;
      const amount = document.createElement("span");
      amount.className = "bubble-amount";
      amount.textContent = data.amount;
      title.appendChild(name);
      title.appendChild(amount);
      content.appendChild(title);

      const detail = document.createElement("div");
      detail.className = "bubble-detail";
      const effects = data.effects.flatMap(text => EFFECT_KEYWORDS[text] || [text]);
      detail.appendChild(buildDetailColumn("effects", effects.length ? effects : ["미확인"]));
      detail.appendChild(buildDetailColumn("side effects", data.sideEffects.length ? data.sideEffects : ["미확인"]));
      content.appendChild(detail);

      bubble.appendChild(content);

      bubble.addEventListener("mouseenter", () => activate(id));
      bubble.addEventListener("mouseleave", () => deactivate());
      bubble.tabIndex = 0;
      bubble.setAttribute("role", "button");
      bubble.setAttribute("aria-label", `${data.name} 성분 정보`);
      bubble.addEventListener("focus", () => activate(id));
      bubble.addEventListener("blur", () => deactivate());
    }

    diagramEl.appendChild(bubble);
    bubbleEls.set(id, bubble);
    data._id = id;
  });
}

function buildDetailColumn(heading, items) {
  const col = document.createElement("div");
  col.className = "detail-col";
  const h = document.createElement("div");
  h.className = "detail-heading";
  h.textContent = heading;
  col.appendChild(h);
  const ul = document.createElement("ul");
  items.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = `• ${text}`;
    ul.appendChild(li);
  });
  col.appendChild(ul);
  return col;
}

function activate(hoveredId) {
  const hovered = bubbleData.find((d) => d._id === hoveredId);
  const hoveredEl = bubbleEls.get(hoveredId);
  hoveredEl.classList.add("is-active");

  const grownSize = Math.min(Math.max(hovered.size * 1.8, 46), 68);
  applyGeometry(hoveredEl, hovered.cx, hovered.cy, grownSize);

  bubbleData.forEach((data) => {
    if (data._id === hoveredId) return;
    const el = bubbleEls.get(data._id);

    let dx = data.cx - hovered.cx;
    let dy = data.cy - hovered.cy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    dx /= dist;
    dy /= dist;

    const newSize = data.size * NEIGHBOUR_SHRINK;
    const newCx = data.cx + dx * PUSH_DISTANCE;
    const newCy = data.cy + dy * PUSH_DISTANCE;

    applyGeometry(el, newCx, newCy, newSize);
  });
}

function deactivate() {
  bubbleData.forEach((data) => {
    const el = bubbleEls.get(data._id);
    el.classList.remove("is-active");
    applyGeometry(el, data.cx, data.cy, data.size);
  });
}

async function load() {
  const id = qs("id");
  if (!id) {
    renderError(gridEl, "제품을 찾을 수 없습니다.");
    return;
  }

  renderLoading(gridEl, "제품 정보를 불러오는 중...");
  try {
    const product = await Api.getProduct(id);
    buildLayout();
    renderProduct(product);
  } catch (err) {
    renderError(gridEl, "제품 정보를 불러오지 못했습니다.", load);
  }
}

initBackLink("products.html");
load();
