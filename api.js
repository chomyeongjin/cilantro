/* API client. POST /api/recommendations accepts age, optional gender and goals.
 * Returns version:2, selections, 0–3 saved-product items, totalCandidates,
 * unmatchedGoals, ageGuidance, status, message and notices.
 * Items use actual product IDs/images/detail links and reviewed reasons.
 * No fixed fallback, invented timing, or efficacy score. recommend.js stores
 * the complete response under cilantro:recommendations:v2 for result.js.
 */
const API_BASE = "";

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" }
  });
  if (!res.ok) {
    throw new Error(`${path} → ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    throw new Error(`${path} → ${res.status} ${res.statusText}`);
  }
  return res.json();
}

const Api = {
  getTrending: () => apiGet("/api/trending"),
  getOptions: () => apiGet("/api/options"),
  getCategory: (optionId) => apiGet(`/api/categories/${encodeURIComponent(optionId)}`),
  getProduct: (productId) => apiGet(`/api/products/${encodeURIComponent(productId)}`),
  postRecommendation: (selections) => apiPost("/api/recommendations", selections)
};
