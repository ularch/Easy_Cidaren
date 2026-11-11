import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

from log.log import Log

cache_logger = Log('word_cache')


def _cache_path():
    if getattr(sys, 'frozen', False):
        local_data = os.environ.get('LOCALAPPDATA')
        root = Path(local_data) / 'Easy_Cidaren' if local_data else Path.home() / '.Easy_Cidaren'
    else:
        root = Path(__file__).resolve().parent.parent
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
    """事务写入查词结果, 超限按 FIFO 淘汰; 更新与命中不改变插入顺序。"""
    if not isinstance(result, dict) or limit <= 0:
        return False
    try:
        payload = json.dumps(result, ensure_ascii=False)
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        parts = tuple(str(part) for part in key)
        with closing(sqlite3.connect(path, timeout=1)) as connection, connection:
            # 在读取条数前获取写锁, 避免多个进程同时插入导致超过上限。
            connection.execute('BEGIN IMMEDIATE')
            connection.execute(
                'CREATE TABLE IF NOT EXISTS word_cache ('
                'course TEXT NOT NULL, unit TEXT NOT NULL, word TEXT NOT NULL, '
                'response TEXT NOT NULL, PRIMARY KEY (course, unit, word))'
            )
            updated = connection.execute(
                'UPDATE word_cache SET response = ? WHERE course = ? AND unit = ? AND word = ?',
                (payload, *parts),
            )
            if updated.rowcount == 0:
                connection.execute(
                    'INSERT INTO word_cache (course, unit, word, response) VALUES (?, ?, ?, ?)',
                    (*parts, payload),
                )
            # 旧版本的表已自带 rowid, 无需新增字段或重建数据库。
            count = connection.execute('SELECT COUNT(*) FROM word_cache').fetchone()[0]
            if count > limit:
                connection.execute(
                    'DELETE FROM word_cache WHERE rowid IN ('
                    'SELECT rowid FROM word_cache ORDER BY rowid LIMIT ?)',
                    (count - limit,),
                )
        return True
    except (OSError, sqlite3.Error, ValueError, TypeError) as error:
        cache_logger.logger.warning(f'保存本地查词缓存失败: {error}')
        return False
