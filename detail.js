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

const MAX_BUBBLE = 46;
const MIN_BUBBLE = 17;
const PUSH_DISTANCE = 6;
const NEIGHBOUR_SHRINK = 0.82;

// Bubbles are positioned in the same 0–100 (% of container width) space as
// the diagram itself. The visible halo ring is bigger than that box —
// detail.css's .diagram-halo uses `inset:-11%`, so its true radius is
// 50 + 11 = 61 in this space. DIAGRAM_RADIUS stays a few units under that
// so bubbles never touch the ring, let alone poke past it.
const DIAGRAM_CENTER = 50;
const DIAGRAM_RADIUS = 58;
const BUBBLE_GAP = 3;

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
    </section>
  `;
}

function renderProduct(product) {
  titleEl.textContent = product.categoryLabel;
  document.title = `Cilantro — ${product.brand} ${product.product}`;

  if (backLinkEl && product.categoryId) {
    backLinkEl.href = `category.html?id=${encodeURIComponent(product.categoryId)}`;
  }

  document.getElementById("detail-brand").textContent = product.brand;
  document.getElementById("detail-product-name").textContent = product.product;

  const bottle = document.getElementById("detail-bottle");
  bottle.src = product.image;
  bottle.alt = `${product.brand} ${product.product}`;

  const pillWidth = pillWidthFor(product.pillSizeMm);
  document.getElementById("detail-pill").style.width = pillWidth + "px";
  document.getElementById("detail-ruler").style.width = pillWidth + "px";
  document.getElementById("detail-size-caption").textContent = product.pillSizeMm
    ? `${product.pillSizeMm}mm`
    : "";

  const forList = document.getElementById("detail-for-list");
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
      "mg 환산 가능한 성분의 상대 함량을 표시합니다. 작은 원은 확대 표시하며 전체 구성비는 아닙니다. 단위가 달라 비교할 수 없는 성분은 가장 작은 원으로 표시합니다.";
  }
}

// Spirals outward from the diagram center, ring by ring, trying several
// angles per ring, until it finds a spot that (a) stays fully inside the
// containment circle and (b) doesn't overlap any bubble placed so far. If a
// size is simply too crowded to fit anywhere, it shrinks and retries rather
// than falling back to an overlapping or out-of-bounds position.
function placeBubble(size, placed, seedIndex, depth) {
  depth = depth || 0;

  if (!placed.length) {
    return { cx: DIAGRAM_CENTER, cy: DIAGRAM_CENTER, size };
  }

  const angleCount = 28;
  const angleOffset = (seedIndex * 47) % 360;
  const radiusStep = 2;
  const maxRadius = DIAGRAM_RADIUS - size / 2;

  for (let radius = 4; radius <= maxRadius; radius += radiusStep) {
    for (let a = 0; a < angleCount; a++) {
      const angle = ((angleOffset + (360 / angleCount) * a) * Math.PI) / 180;
      const cx = DIAGRAM_CENTER + radius * Math.cos(angle);
      const cy = DIAGRAM_CENTER + radius * Math.sin(angle);
      const collides = placed.some((p) => Math.hypot(cx - p.cx, cy - p.cy) < (p.size + size) / 2 + BUBBLE_GAP);
      if (!collides) return { cx, cy, size };
    }
  }

  if (depth >= 6 || size <= 6) {
    // Last resort for pathologically crowded diagrams: land it at minimum
    // size rather than leaving it unplaced.
    return { cx: DIAGRAM_CENTER, cy: DIAGRAM_CENTER, size: Math.max(size * 0.6, 6) };
  }
  return placeBubble(size * 0.85, placed, seedIndex, depth + 1);
}

function layoutIngredients(ingredients) {
  const maxWeight = Math.max(...ingredients.map(ing => ing.weight ?? ing.pct ?? 0), 0) || 1;

  const placed = [];

  ingredients.forEach((ing, index) => {
    const requestedSize = Math.max(
      MIN_BUBBLE,
      Math.min(MAX_BUBBLE, Math.sqrt((ing.weight ?? ing.pct ?? 0) / maxWeight) * MAX_BUBBLE)
    );
    const { cx, cy, size } = placeBubble(requestedSize, placed, index);

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

function applyGeometry(el, cx, cy, size) {
  // No clamping to the container's own 0–100 box: placeBubble() already keeps
  // every bubble inside the (larger) halo circle, and .ingredient-diagram has
  // no overflow:hidden — clamping here would just shove correctly-placed
  // bubbles back toward the center and re-introduce overlaps.
  el.style.left = (cx - size / 2) + "%";
  el.style.top = (cy - size / 2) + "%";
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

  bubbleData = layoutIngredients(ingredients);

  const halo = document.createElement("div");
  halo.className = "diagram-halo";
  diagramEl.appendChild(halo);

  bubbleData.forEach((data, i) => {
    const id = data.id || `dot-${i}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble" + (data.interactive ? " is-interactive" : "");
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
