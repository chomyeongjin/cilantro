/* ==========================================================================
   Cilantro — products.js
   Renders the three option rows (영양제 종류 / 기대효과 / 나이대) from the
   backend and handles single-select-per-row toggling. Selecting an option
   navigates to its generic comparison page: category.html?id=<optionId>.
   pill_sample.png is kept as the static icon for every option, per request.
   ========================================================================== */

const PILL_IMG = "images/pill_sample.png";

const ROW_LABELS = {
  type: "영양제 종류",
  effect: "기대효과",
  age: "나이대"
};

const selections = { type: null, effect: null, age: null };

const rowsEl = document.getElementById("option-rows");

function renderRows(options) {
  rowsEl.innerHTML = "";

  Object.keys(ROW_LABELS).forEach((rowId) => {
    const items = options[rowId] || [];
    if (!items.length) return;

    const divider = document.createElement("hr");
    divider.className = "divider";
    rowsEl.appendChild(divider);

    const rowEl = document.createElement("div");
    rowEl.className = "option-row";
    rowEl.dataset.row = rowId;

    items.forEach((option) => {
      const btn = document.createElement("button");
      btn.className = "option-item";
      btn.type = "button";
      btn.dataset.value = option.id;

      const imgWrap = document.createElement("span");
      imgWrap.className = "option-item-img";
      const img = document.createElement("img");
      img.src = PILL_IMG;
      img.alt = option.label;
      imgWrap.appendChild(img);
      btn.appendChild(imgWrap);

      const text = document.createElement("span");
      text.textContent = option.label;
      btn.appendChild(text);

      btn.addEventListener("click", () => {
        selectOption(rowId, option.id, btn, rowEl);
        window.location.href = `category.html?id=${encodeURIComponent(option.id)}`;
      });

      rowEl.appendChild(btn);
    });

    rowsEl.appendChild(rowEl);
  });

  const closingDivider = document.createElement("hr");
  closingDivider.className = "divider";
  rowsEl.appendChild(closingDivider);
}

function selectOption(rowId, value, btn, rowEl) {
  rowEl
    .querySelectorAll(".option-item.is-selected")
    .forEach((el) => el.classList.remove("is-selected"));

  selections[rowId] = value;
  btn.classList.add("is-selected");
}

async function load() {
  renderLoading(rowsEl, "옵션을 불러오는 중...");
  try {
    const options = await Api.getOptions();
    renderRows(options);
  } catch (err) {
    renderError(rowsEl, "옵션을 불러오지 못했습니다.", load);
  }
}

load();
