/* ==========================================================================
   Cilantro — api.js
   All backend calls for the deploy build live here. No mock data — every
   page fetches from these endpoints and renders whatever comes back.

   Swap API_BASE to the real backend origin (or leave "" if this frontend is
   served from the same origin as the API).

   ---------------------------------------------------------------------
   Expected backend contract
   ---------------------------------------------------------------------

   GET {API_BASE}/api/trending
     -> [
          {
            id: string,              // stable slug, e.g. "ritual-essential-teens"
            rank: number,             // 1 = highest recent 7-day mean interest
            name: string,
            image: string,            // absolute or root-relative image URL
            what: string,             // what the supplement is
            why: string,              // recent news context; not proven causality
            whySources: [{ title: string, url: string, publishedAt: string, publisher: string }],
            how: {
              summary: string,        // e.g. "지난 4개월간 검색량이 꾸준히 상승"
              chart: [{ label: string, value: number | null }] // daily 0–100; null = missing
            }
          },
          ...                          // 6-7 items total
        ]

   GET {API_BASE}/api/options
     -> {
          type:   [{ id: string, label: string }],   // 영양제 종류
          effect: [{ id: string, label: string }],    // 기대효과
          age:    [{ id: string, label: string }]      // 나이대
        }

   GET {API_BASE}/api/categories/{optionId}
     -> {
          id: string,
          label: string,               // display name, e.g. "Omega-3"
          products: [
            {
              id: string,               // product slug, used by /api/products/{id}
              brand: string,
              product: string,          // product name
              image: string,
              mainEffects: [string],    // shown as the "main effects" bullet list
              pillSizeMm: number        // real capsule length in millimetres
            },
            ...
          ]
        }

   GET {API_BASE}/api/products/{productId}
     -> {
          id: string,
          brand: string,
          product: string,
          image: string,
          pillSizeMm: number,
          categoryId: string,            // e.g. "omega3" — lets the page link back to its category
          categoryLabel: string,         // e.g. "Omega-3" — shown as the page title
          for: [string],                // who it's recommended for
          buyLink: string,               // external purchase URL
          ingredients: [                 // top 4-5, pre-sorted by pct desc
            {
              id: string,
              name: string,
              rank: number,
              amount: string,            // e.g. "500mg"
              pct: number,               // share of formula, used for bubble size
              effects: [string],
              sideEffects: [string]
            }
          ]
        }

   POST {API_BASE}/api/recommendations
     <- {
          age: string | null,      // selected age-range option id (recommend.html "age" radios),
                                    // e.g. "kids" | "teens" | "20s" | "30s-40s" | "50s-60s" | "70-plus";
                                    // null if the user left it unselected
          gender: string | null,   // selected gender option id: "male" | "female" | "non-binary";
                                    // null if unselected
          goals: [string]          // selected "wellness goals" checkbox ids, e.g. "immunity",
                                    // "energy-vitality", "eye-health", "digestive-health",
                                    // "sleep-stress", "skin-health" (same ids as products.js'
                                    // effect row); [] if none checked
        }
     -> {
          received: boolean,
          items: [                 // exactly 3 picks, backend/recommendations.py — a fixed rule
                                    // (wellness goal -> candidate supplements) picks from the same
                                    // 6-item "type" taxonomy products.js uses. age/gender are
                                    // accepted but not used to rank picks yet (no real basis for
                                    // that rule, so it isn't faked — see recommendations.py).
            {
              id: string,           // supplement "type" id, e.g. "magnesium" — same ids as
                                     // products.js' OPTIONS.type; recommend.js/result.js use it to
                                     // look up a local pill icon (images/pills/pillX_Y.png), since
                                     // the response itself carries no image
              name: string,         // 영양제 종류 (display name), e.g. "magnesium"
              timing: string,       // 추천 섭취 시간, free text e.g. "취침 전, 밤 21~22시" —
                                     // result.js scans it for 아침/밤 keywords to position the
                                     // timing-track dot (no separate structured time field)
              description: string,  // 간단한 영양제 설명
              link: string          // 해당 영양제 제품 설명 페이지 링크, e.g.
                                     // "category.html?id=magnesium" (already relative — use as-is
                                     // for the <a href>)
            }
          ]
        }

   Flow: recommend.js POSTs the form above on submit, stores the returned `items` in
   sessionStorage under "cilantro:recommendations", then navigates to result.html.
   result.js reads that key to render its 3 cards — there's no separate GET; the POST
   response above is the only source of result.html's data, so reloading result.html
   re-reads sessionStorage rather than hitting the network again.
   ========================================================================== */

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
