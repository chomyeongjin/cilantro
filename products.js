/* ==========================================================================
   Cilantro — products.js
   Renders the three option rows (영양제 종류 / 기대효과 / 나이대) and handles
   single-select-per-row toggling. Selecting an option navigates to its
   generic comparison page: category.html?id=<optionId>.
   Each option has its own icon: images/pills/pill<row>_<col>.png.
   ========================================================================== */

const ROW_LABELS = {
  type: "영양제 종류",
  effect: "기대효과",
  age: "나이대"
};

const OPTIONS = {
  type: [
    { id: "omega3", label: "Omega-3", image: "images/pills/pill1_1.png" },
    { id: "vitamin-b", label: "vitamin B", image: "images/pills/pill1_2.png" },
    { id: "vitamin-c", label: "vitamin c", image: "images/pills/pill1_3.png" },
    { id: "magnesium", label: "magnesium", image: "images/pills/pill1_4.png" },
    { id: "probiotics", label: "probiotics", image: "images/pills/pill1_5.png" },
    { id: "lutein", label: "lutein", image: "images/pills/pill1_6.png" }
  ],
  effect: [
    { id: "immunity", label: "Immunity", image: "images/pills/pill2_1.png" },
    { id: "energy-vitality", label: "Energy & Vitality", image: "images/pills/pill2_2.png" },
    { id: "eye-health", label: "eye health", image: "images/pills/pill2_3.png" },
    { id: "digestive-health", label: "Digestive health", image: "images/pills/pill2_4.png" },
    { id: "sleep-stress", label: "Sleep & Stress", image: "images/pills/pill2_5.png" },
    { id: "skin-health", label: "skin health", image: "images/pills/pill2_6.png" }
  ],
  age: [
    { id: "kids", label: "Kids", image: "images/pills/pill3_1.png" },
    { id: "teens", label: "Teens", image: "images/pills/pill3_2.png" },
    { id: "20s", label: "20s", image: "images/pills/pill3_3.png" },
    { id: "30s-40s", label: "30s & 40s", image: "images/pills/pill3_4.png" },
    { id: "50s-60s", label: "50s & 60s", image: "images/pills/pill3_5.png" },
    { id: "70-plus", label: "70+", image: "images/pills/pill3_6.png" }
  ]
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
      img.src = option.image;
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
  // btn.classList.add("is-selected");
}

renderRows(OPTIONS);
