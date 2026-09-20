/* Saved-product candidates; no fixed three-item fallback or invented timings. */
const RESULTS_KEY = "cilantro:recommendations:v2";
const gridEl = document.getElementById("result-grid");
const summaryEl = document.getElementById("result-summary");
const GOAL_LABELS = { immunity: "면역", "energy-vitality": "에너지·활력", "eye-health": "눈 건강", "digestive-health": "소화 건강", "sleep-stress": "수면·스트레스", "skin-health": "피부 건강" };
function node(tag, text, cls) {
  const el = document.createElement(tag); el.textContent = text;
  if (cls) el.className = cls;
  return el;
}
function render(r) {
  gridEl.replaceChildren(); summaryEl.replaceChildren();
  const selected = [r.selections.age, r.selections.gender, ...r.selections.goals.map(g => GOAL_LABELS[g] || g)].filter(Boolean).join(" · ");
  summaryEl.append(node("p", r.message), node("p", `선택: ${selected} · 후보 ${r.totalCandidates}개 중 ${r.items.length}개 표시`));
  r.notices.forEach(n => summaryEl.appendChild(node("p", n)));
  if (r.unmatchedGoals.length) summaryEl.appendChild(node("p", `현재 표시 후보에 연결되지 않은 목적: ${r.unmatchedGoals.map(g => g.label).join(", ")}`));
  if (!r.items.length && r.ageGuidance) {
    const a = node("a", "연령별 영양 근거 보기"); a.href = `category.html?id=${encodeURIComponent(r.selections.age)}`; summaryEl.appendChild(a);
  }
  r.items.forEach(item => {
    const card = node("article", "", "result-card"), top = node("div", "", "result-card-top"), body = node("div", "", "result-card-body");
    const img = document.createElement("img"); img.src = item.image; img.alt = item.name; top.appendChild(img);
    body.append(node("h2", item.name, "result-name"), node("p", item.matchedGoals.map(g => GOAL_LABELS[g] || g).join(" · "), "result-goals"));
    body.appendChild(node("p", item.eligibilityLabel, "result-eligibility"));
    (item.reviewNotes || []).forEach(w => body.appendChild(node("p", w.text, "result-review-warning")));
    item.reasons.forEach(reason => {
      const amounts = reason.ingredients.map(f => f.amount == null ? f.name : `${f.name} ${f.unit === "CFU" ? `${f.amount / 100000000}억 CFU` : `${f.amount}${f.unit}`}`);
      body.appendChild(node("p", `${reason.basis === "nutrient_function" ? "성분 기능" : "제품 표시"} · ${reason.reason} (${amounts.join(" · ")})`, "result-desc"));
    });
    if (item.serving) body.appendChild(node("p", `함량 기준: ${item.serving.value}`, "result-desc"));
    const details = document.createElement("details"); details.appendChild(node("summary", "연결 근거·주의사항"));
    item.ageReasons.forEach(a => details.appendChild(node("p", a.reason)));
    [...item.warnings.map(w => w.value), ...item.unknowns].forEach(w => details.appendChild(node("p", w)));
    [...new Set(item.reasons.map(m => m.sourceUrl).filter(Boolean))].forEach(url => {
      if (!url.startsWith("https://")) return;
      const a = node("a", "출처 확인"); a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer"; details.append(a, document.createElement("br"));
    });
    const a = node("a", "제품 상세 보기", "result-link"); a.href = `detail.html?id=${encodeURIComponent(item.id)}`;
    body.append(details, a); card.append(top, body); gridEl.appendChild(card);
  });
}
function load() {
  try {
    const r = JSON.parse(sessionStorage.getItem(RESULTS_KEY));
    if (!r || r.version !== 2 || r.policyVersion !== 3 || !Array.isArray(r.items)) throw new Error("No current survey");
    render(r);
  } catch {
    gridEl.replaceChildren(); summaryEl.replaceChildren(node("p", "현재 설문 결과가 없습니다. 설문을 진행해주세요."));
  }
  // const a=node("a","선택 바꾸기");a.href="recommend.html";summaryEl.appendChild(a);
  const a = node("a", "선택 바꾸기 >");
  a.href = "recommend.html";
  a.style.display = "block";
  a.style.textAlign = "right";
  a.style.marginTop = "13px";
  a.style.marginRight = "5px";
  a.style.textDecoration = "underline";
  a.style.fontSize = "14px";

  gridEl.before(a);
}
initBackLink("recommend.html"); load();
