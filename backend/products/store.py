"""Versioned drafts/publications. A failed refresh never erases approved facts."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import database_path
from .models import Analysis, Source, validate_evidence

SCHEMA = '''
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL, payload TEXT NOT NULL,
    created_at TEXT NOT NULL, UNIQUE(product_id, fingerprint)
);
CREATE TABLE IF NOT EXISTS publications (
    product_id TEXT PRIMARY KEY, analysis_id INTEGER NOT NULL REFERENCES analyses(id),
    reviewer TEXT NOT NULL, reviewed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, started_at TEXT NOT NULL,
    finished_at TEXT, state TEXT NOT NULL, result TEXT
);
'''


def now():
    return datetime.now(timezone.utc).isoformat()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


@contextmanager
def connection(path=None):
    path = Path(path) if path is not None else database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        conn.executescript(SCHEMA)
        with conn:
            yield conn
    finally:
        conn.close()


def save_listings(listings, path=None):
    with connection(path) as conn:
        for listing in listings:
            conn.execute('INSERT INTO listings VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE '
                         'SET payload=excluded.payload, updated_at=excluded.updated_at',
                         (listing['id'], dumps(listing), now()))


def save_registrations(listings, update_existing=False, path=None):
    """An unchanged import is a no-op; changed IDs require explicit replacement."""
    counts = {'created': 0, 'updated': 0, 'unchanged': 0}
    with connection(path) as conn:
        # Serialize concurrent registrars before checking for conflicting IDs.
        conn.execute('BEGIN IMMEDIATE')
        for listing in listings:
            row = conn.execute('SELECT payload FROM listings WHERE id=?', (listing['id'],)).fetchone()
            if row:
                previous = json.loads(row['payload'])
                if previous.get('source') != 'manual-manufacturer':
                    raise ValueError('다른 수집 경로의 제품 ID는 덮어쓸 수 없습니다.')
                if previous.get('raw') == listing['raw']:
                    counts['unchanged'] += 1
                    continue
                if not update_existing:
                    raise ValueError('이미 등록된 ID의 내용이 다릅니다. 새 제품은 새 ID로 등록하거나 --update-existing을 사용하세요.')
                counts['updated'] += 1
            else:
                counts['created'] += 1
            conn.execute('INSERT INTO listings VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE '
                         'SET payload=excluded.payload, updated_at=excluded.updated_at',
                         (listing['id'], dumps(listing), now()))
    return counts


def get_listing(product_id, path=None):
    with connection(path) as conn:
        row = conn.execute('SELECT payload FROM listings WHERE id=?', (product_id,)).fetchone()
    return json.loads(row['payload']) if row else None


def list_listings(path=None):
    with connection(path) as conn:
        return [json.loads(row['payload']) for row in conn.execute('SELECT payload FROM listings ORDER BY id')]


def fingerprint(listing, sources, variant_note, model, prompt_version, provider='openai'):
    # Retrieval timestamps alone must not cause another paid analysis.
    content = {'productId': listing['id'], 'productName': listing['product'],
               'productUrl': listing.get('productUrl'), 'buyLink': listing.get('buyLink'),
               'source': listing.get('source'),
               'variantNote': variant_note, 'provider': provider, 'model': model, 'promptVersion': prompt_version,
               'sources': [s.model_dump(exclude={'retrievedAt'}) for s in sources]}
    return hashlib.sha256(dumps(content).encode()).hexdigest()


def existing_draft(product_id, digest, path=None):
    with connection(path) as conn:
        row = conn.execute('SELECT id FROM analyses WHERE product_id=? AND fingerprint=?',
                           (product_id, digest)).fetchone()
    return row['id'] if row else None


def save_draft(listing, analysis, sources, provenance, variant_note, digest, path=None):
    validate_evidence(analysis, sources)
    payload = {'listing': listing, 'analysis': analysis.model_dump(),
               'sources': [s.model_dump() for s in sources], 'provenance': provenance,
               'variantNote': variant_note}
    with connection(path) as conn:
        conn.execute('INSERT OR IGNORE INTO analyses(product_id,fingerprint,payload,created_at) VALUES(?,?,?,?)',
                     (listing['id'], digest, dumps(payload), now()))
        return conn.execute('SELECT id FROM analyses WHERE product_id=? AND fingerprint=?',
                            (listing['id'], digest)).fetchone()['id']


def draft(analysis_id, path=None):
    with connection(path) as conn:
        row = conn.execute('SELECT * FROM analyses WHERE id=?', (analysis_id,)).fetchone()
    if not row:
        raise ValueError('분석 ID를 찾을 수 없습니다.')
    return {'analysisId': row['id'], 'fingerprint': row['fingerprint'],
            'createdAt': row['created_at'], **json.loads(row['payload'])}


def approve(analysis_id, reviewer, path=None):
    if not reviewer.strip():
        raise ValueError('검토자 이름을 입력하세요.')
    item = draft(analysis_id, path)
    analysis = Analysis.model_validate(item['analysis'])
    validate_evidence(analysis, [Source.model_validate(s) for s in item['sources']])
    if not analysis.ingredients:
        raise ValueError('성분이 없는 분석은 공개할 수 없습니다.')
    from .presenter import product_view
    product_view(item)  # Reject contradictory totals before publication.
    with connection(path) as conn:
        conn.execute('INSERT INTO publications VALUES(?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET '
                     'analysis_id=excluded.analysis_id, reviewer=excluded.reviewer, reviewed_at=excluded.reviewed_at',
                     (item['listing']['id'], analysis_id, reviewer.strip(), now()))


def revise(analysis_id, analysis, editor, path=None):
    if not editor.strip():
        raise ValueError('수정자 이름을 입력하세요.')
    previous = draft(analysis_id, path)
    sources = [Source.model_validate(s) for s in previous['sources']]
    validate_evidence(analysis, sources)
    digest = hashlib.sha256(dumps({'parent': previous['fingerprint'], 'analysis': analysis.model_dump()}).encode()).hexdigest()
    provenance = {**previous['provenance'], 'revisedFrom': analysis_id, 'editor': editor.strip()}
    return save_draft(previous['listing'], analysis, sources, provenance,
                      previous['variantNote'], digest, path)


def published(path=None):
    with connection(path) as conn:
        rows = conn.execute('SELECT a.id,a.payload,p.reviewed_at FROM publications p '
                            'JOIN analyses a ON a.id=p.analysis_id ORDER BY p.product_id').fetchall()
    return [{'analysisId': row['id'], 'reviewedAt': row['reviewed_at'], **json.loads(row['payload'])}
            for row in rows]


def stats(path=None):
    with connection(path) as conn:
        counts = {name: conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                  for name in ('listings', 'analyses', 'publications')}
        pending = conn.execute('SELECT COUNT(*) FROM analyses a WHERE NOT EXISTS '
                               '(SELECT 1 FROM publications p WHERE p.analysis_id=a.id)').fetchone()[0]
        last_run = conn.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1').fetchone()
        manual = conn.execute("SELECT COUNT(*) FROM listings WHERE id LIKE 'manual-%'").fetchone()[0]
    return {**counts, 'manualListings': manual, 'unpublishedVersions': pending,
            'lastRun': dict(last_run) if last_run else None}


def start_run(kind, path=None):
    with connection(path) as conn:
        return conn.execute('INSERT INTO runs(kind,started_at,state) VALUES(?,?,?)',
                            (kind, now(), 'running')).lastrowid


def finish_run(run_id, state, result, path=None):
    with connection(path) as conn:
        conn.execute('UPDATE runs SET finished_at=?,state=?,result=? WHERE id=?',
                     (now(), state, dumps(result), run_id))
