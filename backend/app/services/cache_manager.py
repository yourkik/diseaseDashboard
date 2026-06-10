import json
import os
from datetime import datetime
import pytz

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CACHE_FILE = os.path.join(CACHE_DIR, 'disease_cache.json')
INSIGHTS_CACHE_FILE = os.path.join(CACHE_DIR, 'insights_cache.json')

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)

def load_cache():
    ensure_cache_dir()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data):
    ensure_cache_dir()
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def get_disease_cache(disease: str):
    cache = load_cache()
    return cache.get(disease, None)

def update_disease_cache(disease: str, data: list):
    cache = load_cache()
    now_str = datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
    cache[disease] = {
        "last_updated": now_str,
        "data": data
    }
    save_cache(cache)

def load_insights_cache():
    ensure_cache_dir()
    if os.path.exists(INSIGHTS_CACHE_FILE):
        try:
            with open(INSIGHTS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_insights_cache(cache_data):
    ensure_cache_dir()
    with open(INSIGHTS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def get_insights_cache(disease: str):
    cache = load_insights_cache()
    return cache.get(disease, None)

def update_insights_cache(disease: str, data: dict):
    cache = load_insights_cache()
    now_str = datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
    cache[disease] = {
        "last_updated": now_str,
        "data": data
    }
    save_insights_cache(cache)
