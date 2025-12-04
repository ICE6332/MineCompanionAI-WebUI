"""基于 SQLite 的剧情节点持久化存储。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

import aiosqlite
import orjson


class StoryStore:
    """用于存储和读取剧情节点的轻量级持久层。"""

    def __init__(self, db_path: str = "data/world.db") -> None:
        # 使用相对路径，便于跨平台部署
        self.db_path = db_path

    async def init_schema(self) -> None:
        """初始化 SQLite 表结构与索引。"""

        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS story_nodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    node_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_story_session_time ON story_nodes(session_id, timestamp DESC);"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_story_kind ON story_nodes(session_id, kind);"
            )
            await db.commit()

    async def load_history(self, session_id: str, limit: int = 100) -> List[dict]:
        """按时间倒序加载指定会话的最近剧情节点列表。"""

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT node_json
                FROM story_nodes
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            await cursor.close()

        history: List[dict] = []
        for row in rows:
            node_json: str = row[0]
            history.append(orjson.loads(node_json))
        return history

    async def append(self, session_id: str, node: dict) -> None:
        """追加单个剧情节点。"""

        payload = orjson.dumps(node).decode("utf-8")
        created_at = int(time.time())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO story_nodes (id, session_id, timestamp, kind, summary, node_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    node["id"],
                    session_id,
                    node["timestamp"],
                    node["kind"],
                    node["summary"],
                    payload,
                    created_at,
                ),
            )
            await db.commit()
