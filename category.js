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
  const notice = document.getElementById("selection-notice");
  notice.hidden = !category.selectionNotice;
  notice.textContent = category.selectionNotice || "";
  const guidance = document.getElementById("age-guidance");
  guidance.replaceChildren();
  guidance.hidden = !category.ageGuidance;
  if (category.ageGuidance) {
    const heading = document.createElement("h2");
    heading.textContent = category.ageGuidance.title;
    const note = document.createElement("p");
    note.textContent = category.ageGuidance.notice;
    guidance.append(heading, note);
    category.ageGuidance.items.forEach(item => {
      const article = document.createElement("article");
      const title = document.createElement("h3");
      title.textContent = item.title;
      const body = document.createElement("p");
      body.textContent = item.text;
      const source = document.createElement("a");
      source.textContent = "NIH 근거 확인";
      source.href = item.sourceUrl;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      article.append(title, body, source);
      guidance.appendChild(article);
    });
  }
  if (!category.products.length) {
    const empty = document.createElement("p");
    empty.className = "selection-empty";
    empty.textContent = "연결 근거를 확인한 제품이 없습니다.";
    gridEl.appendChild(empty);
    return;
  }

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
        : f.unit === "CFU" ? `${f.name} ${(f.amountPerServing / 100000000).toLocaleString()}억 CFU`
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

    const matches = [...(item.effectMatches || []), ...(item.ageMatches || [])]
      .filter(match => match.id === category.id);
    if (matches.length) {
      const reasons = document.createElement("div");
      reasons.className = "match-reasons";
      matches.forEach(match => {
        const line = document.createElement("p");
        const amounts = (match.ingredients || []).map(f => f.amount == null ? f.name
          : `${f.name} ${f.unit === "CFU" ? `${(f.amount / 100000000).toLocaleString()}억 CFU` : `${f.amount}${f.unit}`}`);
        line.textContent = `${match.basis === "nutrient_function" ? "성분 기능" : match.basis === "adult_label_not_age_efficacy" ? "연령 확인" : "제품 표시"} · ${match.reason}${amounts.length ? ` (${amounts.join(" · ")}, 1회 기준)` : ""}`;
        reasons.appendChild(line);
      });
      (item.selectionCautions || []).forEach(warning => {
        const line = document.createElement("p");
        line.className = "match-caution";
        line.textContent = warning.text;
        reasons.appendChild(line);
      });
      cell.appendChild(reasons);
    }

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
