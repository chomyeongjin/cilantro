from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from service import KST, db_path, read_snapshot, ranked

app = FastAPI(title='Cilantro NAVER Trends', version='1.0.0')


@app.get('/api/trending')
def trending(response: Response, sort: Literal['interest', 'growth'] = 'interest'):
    items = read_snapshot(db_path())
    if items is None:
        raise HTTPException(503, '데이터 준비 중입니다. API 키 설정 후 수집을 실행하세요.')
    response.headers['Cache-Control'] = 'no-store'
    return ranked(items, sort)


@app.get('/api/trending/status')
def status():
    items = read_snapshot(db_path())
    if not items:
        return {'ready': False, 'source': 'NAVER DataLab', 'message': '데이터 준비 중'}
    first = items[0]
    stale = (datetime.now(KST).date() - date.fromisoformat(first['dataThrough'])) > timedelta(days=2)
    return {'ready': True, 'stale': stale, 'source': first['source'],
            'dataThrough': first['dataThrough'], 'fetchedAt': first['fetchedAt'],
            'rankingScope': first['rankingScope'], 'keywordSetVersion': first['keywordSetVersion'],
            'scoreVersion': first['scoreVersion'],
            'excludedFromGrowth': [i['name'] for i in items if not i['growthEligible']]}


@app.get('/health')
def health():
    return {'status': 'ok', 'dataReady': bool(read_snapshot(db_path()))}


@app.get('/api/{unimplemented:path}')
def not_implemented(unimplemented: str):
    raise HTTPException(404, '현재 구현 범위는 트렌딩 API입니다.')


FRONTEND_ROOT = Path(__file__).resolve().parent.parent
# The frontend lives in the repository root. Never expose that entire directory:
# backend credentials, snapshots and Git metadata must remain private.
PUBLIC_FILES = {
    'index.html', 'index.css', 'index.js', 'api.js', 'common.js', 'main.css',
    'products.html', 'products.css', 'products.js',
    'category.html', 'category.css', 'category.js',
    'detail.html', 'detail.css', 'detail.js',
}
app.mount('/images', StaticFiles(directory=FRONTEND_ROOT / 'images'), name='images')


@app.get('/', include_in_schema=False)
def homepage():
    return FileResponse(FRONTEND_ROOT / 'index.html')


@app.get('/{filename}', include_in_schema=False)
def frontend_file(filename: str):
    if filename not in PUBLIC_FILES:
        raise HTTPException(404, '파일을 찾을 수 없습니다.')
    return FileResponse(FRONTEND_ROOT / filename)
