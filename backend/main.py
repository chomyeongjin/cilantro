from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal, Optional
from contextlib import asynccontextmanager
import json
import logging
import os
import sqlite3
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from recommendations import pick_recommendations
from service import KST, db_path, read_snapshot, ranked
from scheduler import Collector
from products.router import router as products_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    collector = Collector()
    app.state.collector = collector
    if os.environ.get('TRENDS_AUTO_COLLECT', '1') == '1':
        collector.start()
    try:
        yield
    finally:
        collector.stop()


app = FastAPI(title='Cilantro API', version='1.2.0', lifespan=lifespan)
app.include_router(products_router)


@app.middleware('http')
async def no_cache_api(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/') or request.url.path == '/health':
        response.headers['Cache-Control'] = 'no-store'
    return response


def snapshot():
    try:
        return read_snapshot(db_path())
    except (sqlite3.Error, json.JSONDecodeError, OSError):
        raise HTTPException(503, '저장된 트렌드 데이터를 읽을 수 없습니다. 잠시 후 다시 시도하세요.') from None


@app.get('/api/trending')
def trending(response: Response, sort: Literal['interest', 'growth'] = 'interest'):
    items = snapshot()
    if not items:
        raise HTTPException(503, '데이터 준비 중입니다. API 키 설정 후 수집을 실행하세요.')
    response.headers['Cache-Control'] = 'no-store'
    return ranked(items, sort)


@app.get('/api/trending/status')
def status():
    items = snapshot()
    collector = getattr(app.state, 'collector', None)
    collection = dict(collector.state) if collector else {'enabled': False, 'running': False}
    if not items:
        return {'ready': False, 'source': 'NAVER DataLab', 'message': '데이터 준비 중', 'collection': collection}
    first = items[0]
    stale = (datetime.now(KST).date() - date.fromisoformat(first['dataThrough'])) > timedelta(days=2)
    return {'ready': True, 'stale': stale, 'source': first['source'],
            'dataThrough': first['dataThrough'], 'fetchedAt': first['fetchedAt'],
            'rankingScope': first['rankingScope'], 'keywordSetVersion': first['keywordSetVersion'],
            'scoreVersion': first['scoreVersion'],
            'excludedFromGrowth': [i['name'] for i in items if not i['growthEligible'] or i['growth7d'] <= 0],
            'interestCount': len(ranked(items)), 'growthCount': len(ranked(items, 'growth')),
            'collection': collection}


class RecommendationRequest(BaseModel):
    age: Optional[Literal['kids', 'teens', '20s', '30s-40s', '50s-60s', '70-plus']] = None
    gender: Optional[Literal['male', 'female', 'non-binary']] = None
    goals: list[Literal['immunity', 'energy-vitality', 'eye-health',
                         'digestive-health', 'sleep-stress', 'skin-health']] = []


@app.post('/api/recommendations')
def submit_recommendation(payload: RecommendationRequest):
    logger.info('Recommendation request: age=%s gender=%s goals=%s',
                payload.age, payload.gender, payload.goals)
    return {'received': True, 'items': pick_recommendations(payload.goals)}


@app.get('/health')
def health():
    return {'status': 'ok', 'dataReady': bool(snapshot())}


@app.get('/api/{unimplemented:path}')
def not_implemented(unimplemented: str):
    raise HTTPException(404, 'API 경로를 찾을 수 없습니다.')


FRONTEND_ROOT = Path(__file__).resolve().parent.parent
# The frontend lives in the repository root. Never expose that entire directory:
# backend credentials, snapshots and Git metadata must remain private.
PUBLIC_FILES = {
    'index.html', 'index.css', 'index.js', 'api.js', 'common.js', 'main.css',
    'products.html', 'products.css', 'products.js',
    'category.html', 'category.css', 'category.js',
    'detail.html', 'detail.css', 'detail.js',
    'recommend.html', 'recommend.css', 'recommend.js',
    'result.html', 'result.css', 'result.js',
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
