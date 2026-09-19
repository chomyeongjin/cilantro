/* ==========================================================================
   Cilantro — category.js
   Generic product-comparison page, driven entirely by the backend.
   URL: category.html?id=<optionId>  (e.g. omega3, vitamin-b, immunity)
   ========================================================================== */

const PILL_IMG = "images/pill_sample.png";

const titleEl = document.getElementById("category-title");
const gridEl = document.getElementById("compare-grid");

function renderGrid(category) {
  titleEl.textContent = category.label;
  document.title = `Cilantro — ${category.label}`;
  gridEl.innerHTML = "";

  category.products.forEach((item) => {
    const cell = document.createElement("a");
    cell.className = "compare-cell";
    cell.href = `detail.html?id=${encodeURIComponent(item.id)}`;

    const head = document.createElement("div");
    head.className = "cell-head";
    const brand = document.createElement("div");
    brand.className = "brand";
    brand.textContent = item.brand;
    const productName = document.createElement("div");
    productName.className = "product-name";
    const shortName = item.product.replace(/\s*·\s*\d+\s*(?:캡슐|정)\s*[×xX]\s*\d+\s*개\s*$/, "");
    productName.textContent = shortName;
    head.appendChild(brand);
    head.appendChild(productName);
    cell.appendChild(head);

    const imageWrap = document.createElement("div");
    imageWrap.className = "cell-image";
    const img = document.createElement("img");
    img.src = item.image;
    img.alt = `${item.brand} ${shortName}`;
    imageWrap.appendChild(img);
    cell.appendChild(imageWrap);

    const sub = document.createElement("div");
    sub.className = "cell-sub";

    const effectsBlock = document.createElement("div");
    effectsBlock.className = "effects";
    const effectsLabel = document.createElement("div");
    effectsLabel.className = "sub-label";
    effectsLabel.textContent = "주요 성분";
    const ul = document.createElement("ul");
    const mainIngredients = item.ingredientFacts?.length
      ? item.ingredientFacts.slice(0, 3).map(f => f.amountPerServing == null ? f.name
        : `${f.name} ${f.amountPerServing}${(f.unit || "").replace("mcg", "μg")}`)
      : (item.mainEffects || []);
    mainIngredients.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = `• ${text.replace(/\s*\/\s*1회\s*$/, "")}`;
      ul.appendChild(li);
    });
    effectsBlock.appendChild(effectsLabel);
    effectsBlock.appendChild(ul);

    const sizeBlock = document.createElement("div");
    sizeBlock.className = "size";
    const sizeLabel = document.createElement("div");
    sizeLabel.className = "sub-label";
    sizeLabel.textContent = "size";
    const pillWidth = pillWidthFor(item.pillSizeMm);
    const pillVisual = document.createElement("div");
    pillVisual.className = "pill-visual";
    pillVisual.style.width = pillWidth + "px";
    const pillImg = document.createElement("img");
    pillImg.src = PILL_IMG;
    pillImg.alt = "actual size";
    pillImg.style.width = pillWidth + "px";
    pillVisual.appendChild(pillImg);
    sizeBlock.appendChild(sizeLabel);
    if (item.pillSizeMm) {
      sizeBlock.appendChild(pillVisual);
    } else {
      const unknown = document.createElement("div");
      unknown.textContent = "미확인";
      sizeBlock.appendChild(unknown);
    }

    sub.appendChild(effectsBlock);
    sub.appendChild(sizeBlock);
    cell.appendChild(sub);

    gridEl.appendChild(cell);
  });
}

async function load() {
  const id = qs("id");
  if (!id) {
    renderError(gridEl, "카테고리를 찾을 수 없습니다.");
    return;
  }

  renderLoading(gridEl, "제품을 불러오는 중...");
  try {
    const category = await Api.getCategory(id);
    renderGrid(category);
  } catch (err) {
    renderError(gridEl, "제품을 불러오지 못했습니다.", load);
  }
}

initBackLink("products.html");
load();
