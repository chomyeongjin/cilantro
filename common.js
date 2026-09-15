/* ==========================================================================
   Cilantro — common.js
   Runs on every page: highlights the current sidebar item, wires the back
   link (browser history, since category.html/detail.html are shared
   templates and don't know a fixed "previous page"), and provides small
   shared helpers for reading the URL and rendering loading/error states.
   ========================================================================== */

const PAGE_MENU_MAP = {
  "index.html": "trending",
  "": "trending",
  "products.html": "products",
  "category.html": "products",
  "detail.html": "products"
};

function initSidebar() {
  const file = location.pathname.split("/").pop();
  const activeMenu = PAGE_MENU_MAP[file];
  if (!activeMenu) return;
  document.querySelectorAll(`.menu-list a[data-menu="${activeMenu}"]`).forEach((el) => {
    el.classList.add("active");
  });
}

function initBackLink(fallbackHref) {
  const backEl = document.querySelector(".back-link");
  if (!backEl) return;
  backEl.addEventListener("click", (e) => {
    e.preventDefault();
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = fallbackHref || "products.html";
    }
  });
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

// Shared "actual size" pill scale: real capsule length (mm) -> display px.
const PILL_MM_TO_PX = 6;
const PILL_MIN_PX = 30;
const PILL_MAX_PX = 70;

function pillWidthFor(mm) {
  if (!mm) return PILL_MIN_PX;
  return Math.max(PILL_MIN_PX, Math.min(PILL_MAX_PX, mm * PILL_MM_TO_PX));
}

function renderLoading(container, text) {
  container.innerHTML = "";
  const el = document.createElement("div");
  el.className = "state-message";
  el.textContent = text || "불러오는 중...";
  container.appendChild(el);
}

function renderError(container, text, onRetry) {
  container.innerHTML = "";
  const el = document.createElement("div");
  el.className = "state-message is-error";
  el.textContent = text || "데이터를 불러오지 못했습니다.";
  container.appendChild(el);

  if (onRetry) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "state-retry";
    retry.textContent = "다시 시도";
    retry.addEventListener("click", onRetry);
    el.appendChild(document.createElement("br"));
    el.appendChild(retry);
  }
}

initSidebar();
