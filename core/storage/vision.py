"""基于 SQLite 的视觉快照持久化存储。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import aiosqlite
import orjson


class VisionStore:
    """用于存储和读取视觉快照的轻量级持久层。"""

    def __init__(self, db_path: str = "data/world.db") -> None:
        # 使用相对路径，便于跨平台部署
        self.db_path = db_path

    async def init_schema(self) -> None:
        """初始化 SQLite 表结构。"""

        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS vision_snapshots (
                    session_id TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                """
            )
            await db.commit()

    async def load(self, session_id: str) -> Optional[dict]:
        """按会话加载视觉快照，未找到则返回 None。"""

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT snapshot_json FROM vision_snapshots WHERE session_id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()

        if row is None:
            return None

        snapshot_json: str = row[0]
        return orjson.loads(snapshot_json)

    async def save(self, session_id: str, snapshot: dict, tick: int) -> None:
        """保存或更新视觉快照，使用 UPSERT 确保幂等。"""

        payload = orjson.dumps(snapshot).decode("utf-8")
        updated_at = int(time.time())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO vision_snapshots (session_id, snapshot_json, tick, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    snapshot_json = excluded.snapshot_json,
                    tick = excluded.tick,
                    updated_at = excluded.updated_at;
                """,
                (session_id, payload, tick, updated_at),
            )
            await db.commit()
