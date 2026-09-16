# Cilantro

기존 루트 HTML/CSS/JS 파일은 원본 그대로 유지하고 FastAPI와 네이버 데이터랩 트렌딩을 연결했습니다.
카테고리·제품 화면과 이미지는 그대로 유지했습니다. 해당 화면의
`/api/options`, `/api/categories/{id}`, `/api/products/{id}`는 아직 미구현(404)입니다.

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
.\.venv\Scripts\python.exe backend\collect.py
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

[화면](http://127.0.0.1:8000) · [API 문서](http://127.0.0.1:8000/docs)

프런트와 API를 같은 서버에서 제공하므로 `api.js`의 `API_BASE`는 빈 문자열입니다.
별도 정적 서버만 실행하면 트렌딩 API는 연결되지 않습니다.
키가 없거나 최초 수집 전이면 API는 503을 반환하고 기존 프런트의 불러오기 실패 메시지가 표시됩니다.
가짜 순위는 만들지 않습니다.
실제 네이버 응답은 인증 정보를 설정한 뒤 수집하여 확인해야 합니다.

별도 터미널에서 아래 명령으로 즉시 수집 후 24시간마다 갱신할 수 있습니다.
프로세스와 컴퓨터가 계속 실행 중이어야 하며 자동 시작은 등록하지 않습니다.

```powershell
.\.venv\Scripts\python.exe backend\collect.py --daily
```

## 트렌딩 동작

- `backend/catalog.json`의 5개 영양제 주제를 한 요청으로 비교합니다.
- 한국 시간 어제까지 최근 90일의 일별 상대 검색 관심도를 수집합니다.
- 검색 관심도: 최근 7일 평균. 상승률: 직전 28일 평균 대비 변화율입니다.
- 상승률 순위에는 양의 변화만 포함하며, 기준 평균이 최대 기준 평균의 5% 미만인 주제는 제외합니다.
- 누락 날짜는 0으로 채우지 않습니다. 불완전한 기간은 해당 순위에서 제외하고 차트 선을 끊습니다.
- 0~100 지수는 실제 검색 횟수·판매량·효능 순위가 아닙니다. 설정된 주제 안에서만 비교합니다.
- SQLite에 요청, 원본 응답, 계산 결과를 함께 저장하고 수집 실패 시 이전 정상 결과를 유지합니다.
- 기준일이 오늘보다 2일 넘게 오래되면 상태 API가 `stale: true`를 반환합니다.
- 현재 이미지는 기존 `images/pill_sample.png`를 쓰는 공통 예시입니다.
- 검색어·이미지 설정 변경 후에는 다시 수집해야 화면에 반영됩니다.

API: `/api/trending?sort=interest`, `/api/trending?sort=growth`,
`/api/trending/status`, `/health`.

기존 화면은 `/api/trending`의 기본 관심도 순위와 What/Why/How 팝업을 사용합니다.
추가 정렬 버튼이나 상태 문구 등 화면 변경은 적용하지 않았습니다.
상승률 정렬과 갱신 상태는 API로 조회할 수 있습니다.

## 구조 및 검증

루트 프런트 구조를 유지하고 `backend/`만 추가했습니다. 서버는 명시된 프런트 파일과
`images/`만 제공하며 `.env`, DB, Git 메타데이터는 제공하지 않습니다.
키와 로컬 데이터, 가상환경은 `.gitignore`에서 제외합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
node --check api.js
node --check index.js
```

테스트는 계산·누락값·수집 실패 시 보존, API 정렬·준비 상태·갱신 지연,
기존 정적 경로와 비공개 파일 접근 차단을 검사합니다.
합성 데이터는 임시 테스트 DB에만 저장하며 실제 화면용 DB에는 넣지 않습니다.
