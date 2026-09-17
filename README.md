# Cilantro

기존 메인 배치를 유지하고 FastAPI와 네이버 데이터랩 트렌딩을 연결했습니다.
트렌드 팝업의 What/Why/How 내용과 차트, 닫기 동작을 개선했습니다.
카테고리·제품 화면과 이미지는 그대로 유지했습니다. 해당 화면의
`/api/options`, `/api/categories/{id}`, `/api/products/{id}` 백엔드를 구현했습니다.
사업자 등록이나 쿠팡 키 없이 공식 제품을 등록할 수 있습니다.
[쿠팡 키 없는 제품 등록·AI 분석 가이드](backend/MANUAL_PRODUCTS_SETUP.md)를 먼저 참고하세요.
선택적인 쿠팡 상품 검색과 전체 API 설명은 [제품별 설명 설정 가이드](backend/PRODUCTS_SETUP.md)에 있습니다.
제품과 원문을 등록하고 AI 분석·검토·공개하기 전에는 실제 제품 목록이 비어 있습니다.

## 실행 (PowerShell, 프로젝트 루트)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# 기존 .env가 있으면 덮어쓰지 않습니다.
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
notepad backend\.env
```

`backend/.env`에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`을 입력합니다.
네이버 클라우드 콘솔의 **NAVER API HUB > Application > 인증 정보**에서
검색어트렌드가 등록된 애플리케이션의 Client ID와 Client Secret을 준비하세요.
환경변수 이름은 그대로 사용하며, 기존 NAVER Developers용 키가 아닌 API HUB 키를 입력합니다.
[공식 호출 명세](https://api.ncloud-docs.com/docs/naver-api-hub-search-trend)에 따라
API HUB 주소와 `X-NCP-APIGW-API-KEY-ID`, `X-NCP-APIGW-API-KEY` 헤더를 사용합니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

[화면](http://127.0.0.1:8000) · [API 문서](http://127.0.0.1:8000/docs)

프런트와 API를 같은 서버에서 제공하므로 `api.js`의 `API_BASE`는 빈 문자열입니다.
별도 정적 서버만 실행하면 트렌딩 API는 연결되지 않습니다.
키가 없거나 최초 수집 전이면 API는 503을 반환하고 기존 프런트의 불러오기 실패 메시지가 표시됩니다.
가짜 순위는 만들지 않습니다.
실제 네이버 응답은 인증 정보를 설정한 뒤 수집하여 확인해야 합니다.

Why의 뉴스에는 [NAVER API HUB 뉴스 검색](https://api.ncloud-docs.com/docs/naver-api-hub-search-news) 권한이 필요합니다.
기본적으로 트렌드와 같은 인증키를 사용합니다. 뉴스 검색이 별도 애플리케이션이라면
`backend/.env`에 `NAVER_NEWS_CLIENT_ID`, `NAVER_NEWS_CLIENT_SECRET`을 추가하세요.
뉴스 인증·통신 실패는 검색 관심도 수집을 막지 않으며, `whyEvidence.errorCode`로 확인할 수 있습니다.

서버가 시작되면 백그라운드에서 즉시 수집하고, 성공 후 24시간마다 갱신합니다.
실패하면 이전 정상 데이터를 유지하며 15분 후 재시도합니다. 첫 수집이 끝나면
브라우저를 새로고침하세요. 프런트는 자동으로 다시 요청하지 않습니다.
서버와 컴퓨터가 계속 실행 중이어야 하며 OS 자동 시작은 등록하지 않습니다.
내장 수집기는 서버 프로세스별로 실행되므로 **worker는 1개**로 실행하세요.
`/api/trending/status`의 `collection`에서 실행 여부·마지막 시도·성공·실패·다음 시도를 확인할 수 있습니다.

외부 스케줄러 또는 아래 별도 수집기를 사용할 때는 서버 실행 전 PowerShell에서
`$env:TRENDS_AUTO_COLLECT = "0"`으로 내장 수집을 끄세요. 이 옵션은 프로세스
환경변수로 설정하며 `backend/.env`에는 인증키만 넣습니다.

```powershell
.\.venv\Scripts\python.exe backend\collect.py --daily
```

## 트렌딩 동작

- `backend/catalog.json`의 5개 영양제 주제를 한 요청으로 비교합니다.
- 한국 시간 어제까지 최근 90일의 일별 상대 검색 관심도를 수집합니다.
- 검색 관심도: 최근 7일 평균. 상승률: 직전 28일 평균 대비 변화율입니다.
- 상승률 순위에는 양의 변화만 포함하며, 기준 평균이 최대 기준 평균의 5% 미만인 주제는 제외합니다.
- 누락 날짜는 0으로 채우지 않고 API에 `null`로 전달합니다. 불완전한 기간은 해당 순위에서 제외합니다.
- 기준일은 모든 주제에 실제로 존재하는 가장 최근 공통 날짜입니다.
- 모든 주제가 관심도 순위에서 제외되는 응답은 저장하지 않고 이전 정상 결과를 유지합니다.
- 0~100 지수는 실제 검색 횟수·판매량·효능 순위가 아닙니다. 설정된 주제 안에서만 비교합니다.
- SQLite에 요청, 원본 응답, 계산 결과를 함께 저장하고 수집 실패 시 이전 정상 결과를 유지합니다.
- 과거 날짜를 `--end YYYY-MM-DD`로 수집해도 라이브 API에는 가장 최신 데이터 기준일의 결과가 표시됩니다.
- 기준일이 오늘보다 2일 넘게 오래되면 상태 API가 `stale: true`를 반환합니다.
- 현재 이미지는 기존 `images/pill_sample.png`를 쓰는 공통 예시입니다.
- 검색어·이미지 설정 변경 후에는 다시 수집해야 화면에 반영됩니다.

API: `/api/trending?sort=interest`, `/api/trending?sort=growth`,
`/api/trending/status`, `/health`.

기존 화면은 `/api/trending`의 기본 관심도 순위와 What/Why/How 팝업을 사용합니다.
추가 정렬 버튼이나 상태 문구 등 화면 변경은 적용하지 않았습니다.
상승률 정렬과 갱신 상태는 API로 조회할 수 있습니다.

### 팝업

- **What**: NIH와 미국 국립안연구소 자료를 바탕으로 한 간단한 영양제 설명과 출처입니다.
  문구와 출처는 `backend/catalog.json`에서 관리합니다.
- **Why**: 데이터 기준일까지 최근 7일의 관련 뉴스 제목·발행일·원문 링크(최대 3개)입니다.
  최신 검색 결과 100건 중 날짜와 제목 관련성을 확인하고 중복을 제거합니다.
  검색 API 결과의 관련 보도이며, 검색 증가의 직접 원인을 입증하거나 SNS 유행을 추정하지 않습니다.
  상승하지 않은 주제·관련 기사 없음·뉴스 조회 실패를 구분합니다. SNS 직접 수집은 포함하지 않습니다.
- **How**: 최근 90일의 일별 상대 검색 강도를 0–100 고정 축의 선 그래프로 표시합니다.
  최근 7일 평균과 날짜별 강도를 표시하고, 날짜 슬라이더로 각 날짜를 탐색할 수 있습니다.
  누락 구간은 선을 끊으며, 기존 첫날/마지막 날 변화율은 제거했습니다.

변경 후 서버를 다시 시작하거나 아래 명령으로 수집한 다음 브라우저를 새로고침하세요.

```powershell
.\.venv\Scripts\python.exe backend\collect.py
```

## 구조 및 검증

루트 프런트 구조를 유지하고 `backend/`만 추가했습니다. 서버는 명시된 프런트 파일과
`images/`만 제공하며 `.env`, DB, Git 메타데이터는 제공하지 않습니다.
키와 로컬 데이터, 가상환경은 `.gitignore`에서 제외합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
node --check api.js
node --check index.js
node --test backend/test_chart.cjs
```

테스트는 계산·누락값·수집 실패 시 보존, API 정렬·준비 상태·갱신 지연,
기존 정적 경로와 비공개 파일 접근 차단을 검사합니다.
합성 데이터는 임시 테스트 DB에만 저장하며 실제 화면용 DB에는 넣지 않습니다.
