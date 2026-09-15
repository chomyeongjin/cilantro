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

  renderDiagram(product.ingredients || []);
}

function layoutIngredients(ingredients) {
  const maxPct = ingredients[0] ? ingredients[0].pct : 1;

  const placed = [];

  ingredients.forEach((ing, index) => {
    const size = Math.max(
      MIN_BUBBLE,
      Math.min(MAX_BUBBLE, Math.sqrt(ing.pct / maxPct) * MAX_BUBBLE)
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
      detail.appendChild(buildDetailColumn("effects", data.effects));
      detail.appendChild(buildDetailColumn("side effects", data.sideEffects));
      content.appendChild(detail);

      bubble.appendChild(content);

      bubble.addEventListener("mouseenter", () => activate(id));
      bubble.addEventListener("mouseleave", () => deactivate());
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
