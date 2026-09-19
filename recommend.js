/* ==========================================================================
   Cilantro — recommend.js
   Collects the "Find your Supplements" selections (age / gender / wellness
   goals) and sends them to the backend on submit. See api.js for the
   /api/recommendations contract.
   ========================================================================== */

const submitBtn = document.getElementById("ask-submit");
const statusEl = document.getElementById("ask-status");

function selectedRadio(name) {
  const checked = document.querySelector(`input[name="${name}"]:checked`);
  return checked ? checked.value : null;
}

function selectedCheckboxes(name) {
  return [...document.querySelectorAll(`input[name="${name}"]:checked`)].map((el) => el.value);
}

function setStatus(text, isError) {
  statusEl.textContent = text;
  statusEl.classList.toggle("is-error", !!isError);
  statusEl.hidden = false;
}

// Key result.js reads on load — must match the one documented in api.js.
const RESULTS_KEY = "cilantro:recommendations";

submitBtn.addEventListener("click", async () => {
  const selections = {
    age: selectedRadio("age"),
    gender: selectedRadio("gender"),
    goals: selectedCheckboxes("goal")
  };

  submitBtn.disabled = true;
  setStatus("전송 중...", false);
  try {
    const response = await Api.postRecommendation(selections);
    sessionStorage.setItem(RESULTS_KEY, JSON.stringify(response.items));
    window.location.href = "result.html";
  } catch (err) {
    setStatus("전송하지 못했습니다. 다시 시도해주세요.", true);
    submitBtn.disabled = false;
  }
});
