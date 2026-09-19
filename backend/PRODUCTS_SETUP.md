# 제품별 설명 백엔드: 준비와 실행

**사업자가 아니거나 쿠팡 API를 사용할 수 없다면 [쿠팡 키 없는 직접 등록 가이드](MANUAL_PRODUCTS_SETUP.md)를 먼저 따른다.**
직접 등록 기능으로 쿠팡 의존을 제거했으며, 아래 쿠팡 후보 검색 경로는 선택 사항이다.

프론트 HTML/CSS/JS와 이미지 파일은 수정하지 않았다. 기존 프론트의
`/api/options`, `/api/categories/{id}`, `/api/products/{id}`에 맞춰 백엔드를 구현했다.
제품 원문 확보 → AI 성분 추출·요약 → 출처 검토 → 분류·조회 순서로 동작한다.

## 1. 먼저 확인할 쿠팡 API 종류

사용자가 전달한 [카테고리 조회 API](https://developers.coupang.com/ko/api/categories/how-to-get-categories)는
WING 판매자 API이다. 카테고리 코드와 하위 구조를 반환하며, 쿠팡 전체 상품의 검색 결과나
영양제 성분표를 반환하지 않는다. [판매자 상품 조회](https://developers.coupang.com/ko/api/products/querying-product)는
등록상품 ID를 사용하는 상품 관리 API이다.

서비스의 상품 후보 검색에는 **쿠팡 파트너스 API 사용 가능 여부**를 먼저 확인해야 한다.
구현된 검색 어댑터는 `GET /v2/providers/affiliate_open_api/apis/openapi/products/search`와
`rCode / data.productData / productId / productName / productUrl` 형식을 사용한다.
HMAC 서명은 [쿠팡 공식 규칙](https://developers.coupang.com/ko/getting-started/open-api-test-guide)을 따른다.
파트너스 상세 문서는 이번 확인에서 비로그인 상태로 공개되지 않았다.
**실계정의 최신 검색 명세, 사용 권한, 호출 한도 및 응답 형식은 키 발급 후 확인해야 하며,
이번 작업에서 쿠팡 실호출 검증은 하지 못했다.**

파트너스 검색 결과는 후보 발견용이다. 검색 상품명이나 검색 API의 요약 정보만으로
EPA/DHA, 원소 마그네슘 함량, 균주, 알약 크기, 효능을 알 수 있다고 가정하지 않는다.
제조사 공식 라벨 또는 동일한 제품의 기능성 표시 자료를 별도로 연결해야 한다.
검색 1회당 최대 10개를 받도록 제한했으며, 쿠팡 전체 상품 전수 수집이나 검색 순위 재현을 보장하지 않는다.

## 2. 직접 준비해야 할 것

### A. 쿠팡 계정과 키 (쿠팡 검색을 쓸 때만)

1. [쿠팡 파트너스](https://partners.coupang.com/)에 로그인한다.
2. 해당 계정에서 파트너스 API 이용 및 상품 검색 API 사용이 가능한지 확인한다.
   메뉴가 없거나 접근이 거절되면 도움말/문의에서 API 권한과 발급 조건을 확인한다.
   이번에 확인하지 못한 가입/실적 조건을 고정값으로 안내하지 않는다.
3. 파트너스용 Access Key와 Secret Key를 발급받는다. WING 판매자 키와 혼용하지 않는다.
4. API 이용 문서에서 검색 경로, 사용 가능한 `limit`, 호출 제한, 상품 데이터 보관·표시 조건,
   파트너스 링크를 사용하는 서비스의 필수 고지 조건을 확인한다. 공개 서비스 적용 전 필요한 고지를 준비한다.
5. 키를 **로컬 `backend/.env`에만** 입력한다. 기존 네이버 키를 덮어쓰지 않는다.

```dotenv
COUPANG_PARTNERS_ACCESS_KEY=발급받은_파트너스_Access_Key
COUPANG_PARTNERS_SECRET_KEY=발급받은_파트너스_Secret_Key
COUPANG_PARTNERS_SUB_ID=
```

WING 키만 있다면 쿠팡 상품 검색 단계는 진행할 수 없다. 공식 제품 직접 등록 경로는 키 없이 사용할 수 있다.
WING 키로는 카테고리 구조 조회만 선택적으로 쓸 수 있다.
이 경우 `COUPANG_SELLER_ACCESS_KEY`, `COUPANG_SELLER_SECRET_KEY`에 WING 키를 넣는다.

### B. AI API 키

SSAFY GMS 키가 있다면 OpenAI 키를 별도로 발급할 필요 없이
[직접 등록 가이드의 GMS 설정](MANUAL_PRODUCTS_SETUP.md)을 사용한다.
`AI_PROVIDER=gms`, `GMS_KEY`, `GMS_MODEL=gpt-4.1`을 설정하며,
사용자에게 제공받은 `https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses`로 호출한다.
아래는 OpenAI에 직접 연결하는 경우이다.

1. [OpenAI API 키 관리](https://platform.openai.com/api-keys)에서 사용할 프로젝트의 키를 준비한다.
2. 프로젝트의 API 사용 권한과 결제/사용 한도를 확인한다.
3. 아래 값을 기존 `backend/.env`에 추가한다.

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=발급받은_API_키
OPENAI_MODEL=gpt-4o-mini
```

[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)의 JSON Schema와
[GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini)를 기본으로 사용한다.
모델은 환경변수로 교체할 수 있다. 첫 실행은 `--max-products 1`로 출력 품질과 비용을 확인한다.
제품명과 연결한 성분표 텍스트는 분석 시 OpenAI API로 전송되며 `store: false`를 사용한다.
`store: false`를 모든 API 로그/보존의 완전한 해제로 해석하지 않는다.
사진 전송이나 제품 이미지 생성은 하지 않는다.

### C. 제품별 원문 출처

제품마다 다음을 준비한다.

- 쿠팡 검색으로 받은 **정확한 제품 ID/이름**.
- 같은 제조사·제품·함량·제형·시장 버전에 해당하는 **공식 라벨 URL**.
- 1회 섭취량, 그 기준의 성분명·함량·단위, 표시된 섭취법, 기능성 문구, 주의사항.
- 제조사 텍스트 페이지가 있으면 URL만 연결할 수 있다.
- 성분표가 사진/PDF 안에만 있거나 JS로만 로딩되면, 그 표를 읽어 텍스트로 옮겨 `text`에 입력한다.
  **현재 수집기는 HTML/텍스트용이며 이미지 OCR·PDF 추출을 자동 수행하지 않는다.**
- 알약 길이는 제조사가 실제 mm를 공개한 경우만 입력 원문에 포함한다. 사진에서 크기를 추정하지 않는다.
- 같은 이름의 다른 국가용 제품, 리뉴얼 전후 제품, 함량이 다른 옵션은 같은 출처로 묶지 않는다.

성분표 출처 연결은 사람이 처음 지정한다. 지정된 HTML URL의 원문 수집과 AI 구조화는 자동이다.
차단된 페이지는 우회하지 않고 오류로 남긴다. 자동 텍스트 수집은 정확한 호스트 허용 목록과 robots.txt를 확인한다.
로그인·쿠키·CAPTCHA가 필요한 페이지의 자동 수집은 구현하지 않았다.

## 3. 실행 순서 — PowerShell, 프로젝트 루트

Python 3.10 이상과 `backend/requirements.txt`의 패키지가 필요하다. 기존 가상환경을 사용한다면
`.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`로 맞춘다.

현재 프론트는 같은 서버에 상대 경로로 API를 호출한다.
반드시 `http://127.0.0.1:8000/products.html`에서 확인한다.
첨부한 `5500/code/products.html`은 별도의 MVP/정적 서버라 이번 백엔드에 자동 연결되지 않는다.

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe backend\collect_products.py status
```

쿠팡 검색 경로는 `coupangConfigured`, AI 분석 단계는 `aiConfigured`를 확인한다.
직접 등록 경로는 쿠팡 키가 필요 없다. 이는 키 존재 여부이며 유효성 검사 결과는 아니다.
키 값은 출력하지 않는다. 프로세스 환경변수가 `.env`보다 우선한다.

### ① 쿠팡에서 후보 검색

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py discover --keyword "오메가3" --limit 10
.\.venv\Scripts\python.exe backend\collect_products.py list
```

결과의 `id`, `product`, `buyLink`를 확인한다. itemId/vendorItemId를 확인할 수 있는 경우
상품 ID에 함께 포함해 옵션을 구별한다. 후보는 아직 공개 페이지에 노출되지 않는다.
다른 성분도 `마그네슘 영양제`, `프로바이오틱스`처럼 검색할 수 있다.

선택적으로 판매자 카테고리 구조를 확인하는 명령:

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py seller-category --code 0
```

### ② 출처 연결 파일 준비

`backend/product_sources.example.json`은 **형식 예시이며 실제 상품 데이터가 아니다.**
이를 참고해 Git에서 제외되는 `backend/data/product_sources.json` 파일을 만든다.
`productId`와 `expectedProductName`은 `list` 결과를 정확히 복사한다.
`variantNote`에 동일한 제품임을 확인한 내용을 적는다.

`text: null`이면 URL의 텍스트를 수집한다. `.env`에 실제 사용한 호스트만 추가한다.

```dotenv
PRODUCT_SOURCE_HOSTS=www.제조사실제도메인.com,라벨제공기관실제도메인.kr
```

자동 수집이 어려우면 `text`를 라벨 원문으로 채운다. 줄바꿈은 JSON의 `\n`으로 표현한다.
URL과 제목은 실제 원문 출처를 유지한다. 번역/요약한 설명이 아닌 성분표 원문을 제공한다.
`sources`에 복수 출처를 추가할 수 있으며, `id`는 제품 안에서 서로 달라야 한다.

### ③ AI 분석

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py analyze --sources backend\data\product_sources.json --max-products 1
```

`analysisId`와 `state: needs_review`를 확인한다. 원문이 바뀌지 않고 모델/프롬프트 버전도 같으면
저장된 분석을 재사용(`cached`)해 중복 호출을 줄인다. 파일에 더 많은 제품이 있으면 `remaining`을 반환한다.
일부 제품 실패는 성공한 초안과 기존 공개 제품을 삭제하지 않는다. 실패가 있으면 명령 종료 코드는 1이다.

### ④ 원문과 AI 결과 검토

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py review --analysis-id 1
```

실제 출력의 분석 ID를 사용한다. 다음을 대조한다.

1. 제조사 라벨이 검색한 쿠팡 제품/옵션/국가 버전과 일치하는가?
2. 1캡슐과 1회 섭취량, 1일 섭취량을 혼동하지 않았는가?
3. mg/mcg/g/IU/CFU 단위와 숫자가 원문과 같은가?
4. 어유 1,000mg을 EPA+DHA 1,000mg으로 바꾸지 않았는가?
5. 마그네슘 화합물 중량을 원소 마그네슘 중량으로 처리하지 않았는가?
6. 원문에 없는 rTG, 장용성, 흡수율 우월성, 질병 치료 효과를 생성하지 않았는가?
7. `partOf`에 전체 오일과 EPA/DHA 등의 포함 관계가 표시되어 중복 합산을 막는가?
8. `totalContentMg`가 **1회분의 전체 제형 중량**인가? 오일 소계/유효성분 합/병 무게라면 null이어야 한다.
9. 효능 문구의 조건·한정 표현을 유지했는가? 특정 나이대 적합성에 명시적인 근거가 있는가?
10. `summary`, `unknowns`가 확인된 사실과 미확인 사항을 제대로 설명하는가?

인용 문장이 원문에 존재하는지는 코드가 검증하지만, 인용의 의미와 제품 매칭까지 자동으로 보장하지 않는다.
첫 공개 전 검토는 이 오류를 막기 위한 운영 단계이다. 건강 관련 설명은 필요 시 관련 전문가와 검토한다.

잘못된 추출값은 `review` 출력의 `analysis` 객체만 별도 JSON으로 복사해 수정하고 새 버전을 만든다.
근거 인용은 실제 원문과 일치해야 하며 원래 버전은 보존된다.

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py revise --analysis-id 1 --analysis-file backend\data\corrected_analysis.json --editor "검토자 이름"
```

### ⑤ 검토 완료한 버전 공개

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py approve --analysis-id 1 --reviewer "검토자 이름" --confirm-label-review
```

수정한 경우에는 새 분석 ID를 사용한다. 기존 제품의 공개 버전은 승인한 시점에만 교체된다.
실수로 교체했다면 이전 분석 ID를 같은 명령으로 다시 승인해 되돌릴 수 있다.

### ⑥ 서버와 화면 확인

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

이미 서버가 실행 중이면 두 개를 띄우지 않는다. 코드 변경 반영에만 재시작이 필요하며,
이후 수집·승인 데이터는 서버 재시작 없이 새로고침으로 반영된다.
이번 제품 수집은 명시적 CLI 배치이다. 서버 시작/공개 GET 요청으로 AI 과금이나 재수집이 발생하지 않는다.
네이버 트렌드 자동 수집은 기존 동작을 유지한다.

## 4. 반환 데이터와 분류 원칙

| API | 용도 |
| --- | --- |
| `GET /api/options` | 영양제 유형·기대효과·나이대 옵션과 검토 완료 제품 수 |
| `GET /api/categories/omega3` | 해당 카테고리의 제품 목록, 기존 카드 필드 호환 |
| `GET /api/categories/all?type=omega3&effect=eye-health` | 교집합 필터, `offset`/`limit` 페이지 조회 |
| `GET /api/products/{id}` | 기존 상세 필드 + `ingredientFacts`, `comparison`, `summary`, `sources` |
| `GET /api/products/compare?ids=ID1,ID2` | 2~6개 제품의 표시된 1회량 기준 비교 |
| `GET /api/products/status` | 설정·수집·분석·공개 상태 |

초기 유형은 MVP의 8종 + 루테인이다. 복합제는 여러 유형에 분류된다.
기능성 카테고리는 검토한 라벨의 기능성 문구에 의해서만 붙인다.
연령 카테고리 역시 명시적인 표시 근거가 필요하다. ‘성인용’을 모든 연령 카테고리에 자동 배정하지 않는다.
확인되지 않은 성분/나이대는 분류하지 않는다. 새 성분 유형은 `products/taxonomy.py`에 확장한다.

AI는 성분명 정규화·섭취 기준 추출·기능성 분류 제안·쉬운 설명을 맡는다.
코드는 단위 변환과 합계를 계산한다. 예를 들어 어유량과 EPA+DHA량을 각각 반환하고,
부모 성분 안에 이미 포함된 자식 성분을 다시 더하지 않는다.
[NIH 오메가3 자료](https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/)도
ALA·EPA·DHA를 구분하므로 단순히 ‘오메가3 몇 mg’으로 모두 합치지 않는다.
이 참고 자료가 개별 판매 제품의 임상적 효과를 검증해주는 것은 아니다.

함량이 많다는 이유로 효능 순위를 매기지 않는다. 함량 미확인은 `null`이며 0과 다르다.
IU/CFU/mL를 mg으로 변환하지 않는다. 한 제품의 표시량을 다른 제품의 동일 효능으로 환산하지 않는다.

## 5. 프론트를 수정하지 않아 남는 표현 제약

- 제품 이미지와 옵션 아이콘은 기존 `pill_sample.png`를 참조한다. 실제 상품 이미지는 이번 범위 밖이다.
- 실제 길이를 모르면 `pillSizeMm: null`이다. 기존 프론트는 기본 크기 이미지를 그리며 실측값을 표시하지 않는다.
  기존 `actual size` 대체 텍스트까지 고치지는 않았다.
- `mainEffects`에는 검토한 표시 기능성을 보내고, 기능성 문구가 없으면 확인한 주요 성분/함량을 보낸다.
- 원형 그래프는 전체 제형 중량을 모르면 `ingredients: []`이다. 성분 구성비나 %DV를 임의로 만들지 않는다.
  모든 성분은 별도 `ingredientFacts`에 있으며, 이 필드는 현재 상세 프론트가 아직 표시하지 않는다.
- 출처·AI 설명·미확인 사항·주의사항·비교 지표도 API에 있지만 현재 화면에는 이를 그리는 UI가 없다.
  기능성 자체는 라벨 표시를 요약한 것이며 치료 효과 검증 결과가 아니다.
- 빈 카테고리는 API에서 안내문과 `products: []`를 반환한다. 현재 프론트는 안내문을 렌더링하지 않아 빈 칸으로 보인다.
- 목록 기본 한도는 100개이다. 다음 페이지는 API에서 제공하지만 기존 프론트에는 페이지 이동 UI가 없다.

## 6. 오류 확인

| 코드/상태 | 확인할 것 |
| --- | --- |
| `COUPANG_PARTNERS_CREDENTIALS_MISSING` | 파트너스 키 두 개를 `.env`에 입력했는지 |
| `COUPANG_HTTP_401`, `COUPANG_HTTP_403` | 키 종류·권한·서명 시각·계정의 검색 API 사용 가능 여부 |
| `COUPANG_HTTP_429` | 계정 호출 한도 확인 후 재시도 |
| `COUPANG_SEARCH_REJECTED`, `COUPANG_SEARCH_INVALID_RESPONSE` | 계정에서 보는 최신 공식 응답 명세 확인 |
| `OPENAI_CREDENTIALS_MISSING`, `OPENAI_HTTP_401` | OpenAI 프로젝트 키/권한 |
| `GMS_CREDENTIALS_MISSING`, `GMS_HTTP_401/403` | `.env`의 GMS_KEY와 SSAFY GMS 사용 권한 |
| `GMS_HTTP_429` | GMS 잔여 사용량/호출 한도 |
| `GMS_HTTP_400` | GMS의 모델명 및 구조화 출력 요청 옵션 지원 여부 |
| `OPENAI_HTTP_429` | API 사용 한도/요금 설정, 호출 간격 |
| `*_CONNECTION_FAILED` | 인터넷·프록시·실행 환경 네트워크 권한. Codex 제한 환경에서는 외부 호출 실패 가능 |
| `SOURCE_HOST_NOT_ALLOWED` | 실제 공식 출처 호스트를 허용 목록에 추가 |
| `SOURCE_ROBOTS_DISALLOWED`, `SOURCE_HTTP_403` | 접근 조건 확인, 허가된 원문 텍스트 제공 |
| `SOURCE_ROBOTS_HTTP_302`, `SOURCE_HTTP_301/302` | 브라우저로 최종 HTTPS 출처 확인 후 정확한 URL/호스트 지정 |
| `SOURCE_TEXT_REQUIRED` | 이미지/PDF 성분표를 검증 가능한 텍스트로 제공 |
| `PRODUCT_VARIANT_NAME_MISMATCH` | 현재 수집 상품명과 `expectedProductName` 대조 |
| `PRODUCT_NOT_REGISTERED` | `register` 또는 `discover`로 제품을 먼저 등록 |
| `REGISTERED_SOURCES_MISMATCH` | 직접 등록 파일을 수정했다면 먼저 `register --update-existing` 실행 |
| `OPENAI_ANALYSIS_VALIDATION_FAILED` | 구조/근거 검증 실패. 더 명확한 해당 제품 성분표 제공 |
| `ready: false`, `publications: 0` | 아직 검토·공개한 제품이 없음 |

제품 데이터와 원문은 `backend/data/products.sqlite3`에 저장되며 Git 및 정적 파일 제공에서 제외된다.
출처 전문과 분석 수정/승인은 로컬 CLI로만 접근한다. API에는 공개용 필드만 노출한다.

검증 명령:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
```

테스트는 임시 DB와 합성 라벨을 사용한다. 테스트 통과는 실제 쿠팡 계정 권한이나 실제 AI 분석 품질의 검증을 대신하지 않는다.
