"""SQLite business storage: immutable complete snapshots + append-only audit/scenarios.

Snapshots deliberately keep source facts, evidence and derived facts together so a
historical scenario is reproducible. LangGraph uses its own checkpoint database.
"""
from __future__ import annotations
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from . import suppliers as directory
from .rfx_intake import blank_checklist
from .store import DATA_DIR, ROOT

LOCK = threading.RLock()
VENDORS = {
    'packright': ('PackRight Industries', 'vendor_a_packright_offer.xlsx'),
    'corrpro': ('CorrPro International', 'vendor_b_corrpro_quote.pdf'),
    'boxworks': ('BoxWorks India Pvt Ltd', 'vendor_c_boxworks_offer.docx'),
    'alphapack': ('AlphaPack Solutions', 'vendor_d_alphapack_rate_card_photo.jpg'),
    'greencarton': ('GreenCarton Co.', 'vendor_e_greencarton_reply.eml'),
}

def now():
    return datetime.now(timezone.utc).isoformat()

def runtime_dir():
    p = Path(os.getenv('AERCHAIN_DATA_DIR', str(ROOT / 'runtime')))
    p.mkdir(parents=True, exist_ok=True)
    return p

@contextmanager
def connect():
    with LOCK:
        db = sqlite3.connect(runtime_dir() / 'business.sqlite', timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
          CREATE TABLE IF NOT EXISTS datasets(version INTEGER PRIMARY KEY, created TEXT, data TEXT);
          CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, created TEXT, actor TEXT, action TEXT, version INTEGER, detail TEXT);
          CREATE TABLE IF NOT EXISTS scenarios(id TEXT PRIMARY KEY, created TEXT, version INTEGER, data TEXT);
          CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, created TEXT, data TEXT);
        ''')
        try:
            yield db
            db.commit()
        finally:
            db.close()

def blank_vendor(vid, name, filename='', email=None, custom=False):
    return {'id': vid, 'name': name, 'file': filename, 'format': Path(filename).suffix[1:] if filename else '',
            'email': email or directory.profile(vid).get('email'), 'custom': custom,
            'quality': 'pending', 'lead': None, 'response_status': 'awaiting_ingestion',
            'facts': [], 'terms': {}, 'questionnaire': {}, 'lines': [], 'documents': [], 'message': ''}

def initial():
    rfx = json.loads((DATA_DIR / 'rfx.json').read_text())
    return {'dataset_version': 1, 'rfx': rfx, 'rfx_status': 'draft', 'rfx_version': 1,
            'draft': None, 'workflow_id': None, 'stage': 'draft',
            'rfx_chat': [], 'rfx_checklist': blank_checklist(), 'rfx_intake_mode': None,
            'supplier_match': None,
            'vendors': {v: blank_vendor(v, n, f) for v, (n, f) in VENDORS.items()},
            'evidence':{}, 'comparison':[], 'exceptions':[], 'clarifications':[]}

def read(version=None):
    with connect() as db:
        row = db.execute('SELECT data FROM datasets WHERE version=?', (version,)).fetchone() if version else db.execute('SELECT data FROM datasets ORDER BY version DESC LIMIT 1').fetchone()
        if row:
            return json.loads(row['data'])
        if version is not None:
            raise KeyError('Dataset version not found')
        data = initial()
        db.execute('INSERT INTO datasets VALUES(?,?,?)', (1, now(), json.dumps(data)))
        return data

def change(action, actor, mutate, expected=None):
    with LOCK:
        data = read()
        if expected is not None and data['dataset_version'] != expected:
            raise ValueError('This dataset changed. Refresh before saving your correction.')
        mutate(data)
        data['dataset_version'] += 1
        with connect() as db:
            db.execute('INSERT INTO datasets VALUES(?,?,?)', (data['dataset_version'], now(), json.dumps(data, allow_nan=False)))
            db.execute('INSERT INTO audit VALUES(?,?,?,?,?,?)', (str(uuid4()), now(), actor, action, data['dataset_version'], json.dumps({'action':action})))
        return data

def save_scenario(result, question='', interpreter='structured_form'):
    result = dict(result, id=str(uuid4()), created_at=now(), question=question, interpreter=interpreter)
    with connect() as db:
        db.execute('INSERT INTO scenarios VALUES(?,?,?,?)', (result['id'], result['created_at'], result['dataset_version'], json.dumps(result)))
    return dict(result, stale=result['dataset_version'] != read()['dataset_version'])

def scenarios():
    current = read()['dataset_version']
    with connect() as db:
        return [dict(json.loads(r['data']), stale=r['version'] != current) for r in db.execute('SELECT * FROM scenarios ORDER BY created DESC')]

def scenario(sid):
    for s in scenarios():
        if s['id'] == sid:
            return s
    raise KeyError('Scenario not found')

def audit():
    with connect() as db:
        return [dict(x) for x in db.execute('SELECT * FROM audit ORDER BY created DESC')]
