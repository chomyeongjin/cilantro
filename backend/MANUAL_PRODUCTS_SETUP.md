# 쿠팡 키 없이 제품 등록하기

사업자 등록과 쿠팡 API 키가 필요 없는 기본 경로이다.
**공식 제품 등록 → 원문 수집 → AI 분석 → 원문 검토 → 공개** 순서로 진행한다.
기존 프론트/이미지와 네이버 트렌드 API는 변경하지 않는다.

## 준비된 실제 제품 예시

`backend/manual_products.example.json`에 다음 공식 제품 페이지를 연결했다.

- [NOW Ultra Omega-3, Bovine Gelatin, 90 Softgels](https://www.nowfoods.com/products/supplements/ultra-omega-3-fish-oil-bovine-gelatin-softgels): 미국 공식 SKU 1661.
- [Life Extension Super Omega-3, 120 softgels](https://www.lifeextension.com/vitamins-supplements/item01982/super-omega-3-epa-dha-fish-oil-sesame-lignans-olive-extract): 미국 공식 Item 01982.

2026-09-17 제품명/포장/URL을 확인했다. 구매 추천이나 효능 검증 목록이 아니다.
등록 파일에는 성분 분석 결과를 미리 넣지 않았다. 자동 수집 가능 여부는 제조사 응답/접근 조건에 따라 달라진다.
국내 유통 제품과 같은 제형·함량이라고 가정하지 않고 미국 공식 버전으로 구별한다.

## 1. 먼저 제품 등록 — API 키 없이 가능

PowerShell, 프로젝트 루트에서 실행한다.

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe backend\collect_products.py register --file backend\manual_products.example.json
.\.venv\Scripts\python.exe backend\collect_products.py list
.\.venv\Scripts\python.exe backend\collect_products.py status
```

등록은 외부 통신이나 AI 호출 없이 로컬 DB에 제품과 출처를 저장한다.
같은 파일을 다시 등록하면 `unchanged`로 처리한다. 이 단계만으로 제품이 공개되지는 않는다.
상태의 `manualListings`는 등록 수, `publications`는 검토 후 공개 수이다.
`coupangConfigured: false`여도 정상이며 `coupangRequired: false`로 표시한다.

## 2. AI 키와 원문 수집 호스트 설정

실제 자동 AI 분석에는 **SSAFY GMS 키** 또는 직접 발급한 OpenAI API 키를 사용할 수 있다.
현재 사용할 경로는 사용자에게 받은 GMS REST 예시의 OpenAI Responses API이다.
기존 `backend/.env`의 네이버 키를 유지하고 아래 설정만 추가한다.

```dotenv
AI_PROVIDER=gms
GMS_KEY=본인의_GMS_키
GMS_MODEL=gpt-4.1
PRODUCT_SOURCE_HOSTS=www.nowfoods.com,www.lifeextension.com
```

요청 주소는 `https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses`이고,
`Authorization: Bearer GMS_KEY` 헤더로 인증한다. GMS 모델 사용 권한/잔여 사용량을 확인한다.
GMS를 사용할 때는 `OPENAI_API_KEY`가 필요 없다. 키를 코드·등록 JSON·Git에 넣지 않는다.
키가 없으면 분석 명령은 원문 수집을 시작하기 전에 `GMS_CREDENTIALS_MISSING`을 반환한다.
쿠팡 키는 어떤 단계에도 필요 없다.

`status` 명령에서 `aiProvider: "gms"`, `aiModel: "gpt-4.1"`, `aiConfigured: true`인지 확인한다.
이는 설정 유무이며 실제 인증 성공 여부는 아니다. `GMS_HTTP_401/403`은 인증/권한,
`GMS_HTTP_429`는 GMS 사용 한도, `GMS_HTTP_400`은 모델과 요청 옵션 지원 여부를 확인한다.
GMS가 실패해도 OpenAI 직접 호출로 자동 전환하지 않는다.

기존 OpenAI 키를 쓰려면 `AI_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL`을 설정한다.
`AI_PROVIDER`를 생략하면 `GMS_KEY`가 있는 경우 GMS를, 없으면 OpenAI를 선택한다.
두 키가 있으면 명시적으로 provider를 지정하는 것이 좋다.
이번 연결은 **GMS의 GPT Responses 경로**이며 Gemini `generateContent`는 추가하지 않았다.
GPT의 구조화 출력과 원문 근거 검증을 유지한다. 모델/JSON Schema 옵션의 실제 GMS 통과 여부는
키를 설정한 뒤 첫 분석으로 확인해야 한다.

분석에 필요한 제품명·성분표는 선택한 GMS 경유 API로 전송된다. `store: false`를 보내지만
GMS 자체의 요청/로그 보존 정책까지 변경하는 설정은 아니다.

`PRODUCT_SOURCE_HOSTS`는 자동 수집할 **정확한 공식 도메인**을 쉼표로 구분한 목록이다.
새 제조사 URL을 추가하면 그 호스트도 추가한다. 다른 페이지로 리다이렉트되면
브라우저로 확인한 최종 URL을 등록하고 호스트 목록도 맞춘다.
호스트 설정이 허용된 URL이라도 robots.txt나 서버가 접근을 제한하면 수집을 중단한다.

## 3. 등록한 같은 파일로 분석

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py analyze --sources backend\manual_products.example.json --max-products 1
```

먼저 한 제품의 출력과 사용량을 확인한다. 이후 `--max-products 2`로 두 제품을 처리할 수 있다.
특정 제품만 선택하려면 `--product-id`를 함께 사용한다. 예를 들어 첫 제조사 수집이 차단되었을 때,
아래 명령은 NOW에 재접속하지 않고 Life Extension 한 제품만 처리한다.

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py analyze --sources backend\manual_products.example.json --product-id manual-life-extension-super-omega3-01982-us --max-products 1
```

`SOURCE_HTTP_403`은 제조사 수집 거절이며 GMS 키 오류가 아니다. 차단을 우회하지 말고
허용된 다른 출처를 사용하거나 직접 확인한 라벨 원문을 `text`에 입력하고 재등록한다.
`GMS_ANALYSIS_VALIDATION_FAILED`는 응답의 중복 성분·함량 기준·출처 인용 등의 검증 실패이다.
검증을 완화하거나 자동으로 공개하지 않으며, 실패한 요청도 AI 사용량을 소비할 수 있다.

동일한 제품/원문/모델/프롬프트의 저장된 분석은 재사용한다.
출력의 `analysisId`와 `needs_review` 또는 `cached` 상태를 확인한다.
구매 URL 변경도 새 버전으로 처리해 이전 링크가 남는 일을 막는다.

## 4. 결과 검토 후 공개

아래 `1`은 예시이다. 실제 반환된 분석 ID로 바꾼다.

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py review --analysis-id 1
.\.venv\Scripts\python.exe backend\collect_products.py approve --analysis-id 1 --reviewer "검토자 이름" --confirm-label-review
```

제품 버전, 1회량, mg/mcg/g/IU/CFU, EPA/DHA와 어유 총량, 원소량과 화합물량,
기능성 문구 및 알약 크기가 원문과 같은지 대조한다.
수정이 필요하면 [기존 가이드의 검토·수정 명령](PRODUCTS_SETUP.md)을 사용한다.
승인 전의 새 분석이나 등록 정보 수정은 기존 공개 데이터를 바꾸지 않는다.

확인은 [제품별 설명 화면](http://127.0.0.1:8000/products.html)에서 한다.
첨부했던 `5500/code/`는 별도 정적 서버이다.

## 제품을 추가하거나 변경할 때

예시 JSON을 참고해 `backend/data/my_products.json`을 만든다. `backend/data/`는 Git에서 제외된다.
각 배열 항목의 필드는 아래와 같다.

| 필드 | 입력할 내용 |
| --- | --- |
| `id` | `manual-브랜드-제품-포장-국가` 형태의 영문 소문자/숫자/하이픈 ID. 다른 제품/제형은 다른 ID |
| `product` | 공식 제품명과 포장 규격 |
| `productUrl` | 해당 버전의 공식 HTTPS 제품 페이지 |
| `buyLink` | 선택 사항. 확인한 구매 HTTPS 주소. 생략하면 공식 제품 페이지 사용 |
| `variantNote` | 국가·SKU·제형·포장 수 등 같은 이름의 다른 제품과 구별할 정보 |
| `sources` | 공식 출처 배열. 각각 `id`, `kind`, `url`, `title`, `text` 필요 |

`sources.kind`는 `manufacturer`, `label`, `regulator` 중 선택한다.
`text: null`은 HTML 텍스트 자동 수집을 뜻한다. 사진/PDF/JS 전용 페이지는
원문 라벨을 정확하게 텍스트로 옮겨 `text`에 넣고 URL은 원래 출처로 유지한다.
이미지 OCR/PDF 자동 해석은 현재 구현 범위 밖이다.
직접 텍스트를 입력한 출처는 호스트 설정 없이 분석할 수 있다.

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py register --file backend\data\my_products.json
.\.venv\Scripts\python.exe backend\collect_products.py analyze --sources backend\data\my_products.json --max-products 1
```

기존 ID의 내용이 달라지면 기본 등록 명령은 오류를 반환한다. 같은 제품의 자료를 정정하는 경우에만:

```powershell
.\.venv\Scripts\python.exe backend\collect_products.py register --file backend\data\my_products.json --update-existing
```

등록하지 않은 새 출처/버전 정보로 바로 분석하면 `REGISTERED_SOURCES_MISMATCH`가 발생한다.
수정한 파일을 먼저 등록하고 분석에도 같은 파일을 사용한다.
파일 중 한 제품에 오류/ID 충돌이 있으면 해당 등록 묶음 전체를 취소한다.

## 화면과 API의 현재 범위

승인한 제품은 기존 유형/기능성/연령 분류 및 상세 API에서 동일하게 조회된다.
미확인 알약 크기·성분 비율은 만들어 넣지 않는다. 이미지에는 기존 자리표시자를 사용한다.
전체 제형 중량이 없으면 원형 성분 그래프가 비어 있을 수 있고,
추가 성분 지표·출처·주의사항 등은 API 필드에만 있다. 자세한 제한은
[기존 가이드](PRODUCTS_SETUP.md)의 ‘프론트를 수정하지 않아 남는 표현 제약’을 참고한다.

실제 AI 분석을 하지 않은 등록 데이터나 합성 테스트 데이터를 공개된 분석 결과로 취급하지 않는다.
