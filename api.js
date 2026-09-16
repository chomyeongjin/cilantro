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

const Api = {
  getTrending: () => apiGet("/api/trending"),
  getOptions: () => apiGet("/api/options"),
  getCategory: (optionId) => apiGet(`/api/categories/${encodeURIComponent(optionId)}`),
  getProduct: (productId) => apiGet(`/api/products/${encodeURIComponent(productId)}`)
};
