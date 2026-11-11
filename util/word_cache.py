import json
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

from log.log import Log

cache_logger = Log('word_cache')


def _cache_path():
    root = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    return root / 'config' / 'word_cache.sqlite3'


def lookup(key):
    """读取本地查词结果, 缺失或损坏时返回 None, 交给调用方重新查词。"""
    try:
        path = _cache_path()
        if not path.is_file():
            return None
        with closing(sqlite3.connect(path, timeout=1)) as connection:
            row = connection.execute(
                'SELECT response FROM word_cache WHERE course = ? AND unit = ? AND word = ?',
                tuple(str(part) for part in key),
            ).fetchone()
        if row:
            result = json.loads(row[0])
            return result if isinstance(result, dict) else None
    except (OSError, sqlite3.Error, ValueError, TypeError) as error:
        cache_logger.logger.warning(f'读取本地查词缓存失败: {error}')
    return None


def save(key, result, limit=2000):
    """事务写入成功查词结果, 最多保存 limit 条; 本地写入失败不打断答题。"""
    if not isinstance(result, dict):
        return False
    try:
        payload = json.dumps(result, ensure_ascii=False)
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        parts = tuple(str(part) for part in key)
        with closing(sqlite3.connect(path, timeout=1)) as connection, connection:
            connection.execute(
                'CREATE TABLE IF NOT EXISTS word_cache ('
                'course TEXT NOT NULL, unit TEXT NOT NULL, word TEXT NOT NULL, '
                'response TEXT NOT NULL, PRIMARY KEY (course, unit, word))'
            )
            count = connection.execute('SELECT COUNT(*) FROM word_cache').fetchone()[0]
            if count >= limit:
                connection.execute(
                    'UPDATE word_cache SET response = ? WHERE course = ? AND unit = ? AND word = ?',
                    (payload, *parts),
                )
            else:
                connection.execute(
                    'INSERT OR REPLACE INTO word_cache (course, unit, word, response) VALUES (?, ?, ?, ?)',
                    (*parts, payload),
                )
        return True
    except (OSError, sqlite3.Error, ValueError, TypeError) as error:
        cache_logger.logger.warning(f'保存本地查词缓存失败: {error}')
        return False
