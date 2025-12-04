"""EngineSession 管理器，负责多会话生命周期的维护。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from core.engine.runtime import WASMRuntime
from core.engine.session import EngineSession
from core.interfaces import EngineSessionManagerInterface
from core.storage.story import StoryStore
from core.storage.vision import VisionStore


class EngineSessionManager(EngineSessionManagerInterface):
    """管理多个 EngineSession，提供获取、回收与批量关闭能力。"""

    def __init__(self, runtime: WASMRuntime, vision_store: VisionStore, story_store: StoryStore) -> None:
        self.runtime = runtime
        self.vision_store = vision_store
        self.story_store = story_store
        self._sessions: dict[str, EngineSession] = {}

    async def get_or_create(
        self,
        session_id: str,
        character_id: str,
        character_card: dict,
        config: dict,
    ) -> EngineSession:
        """获取已存在会话，否则创建并初始化新会话。"""

        session = self._sessions.get(session_id)
        if session is not None and session.initialized:
            return session

        session = EngineSession(session_id=session_id, character_id=character_id)
        await session.initialize(self.runtime, self.vision_store, self.story_store, character_card, config)
        self._sessions[session_id] = session

        return session

    def get(self, session_id: str) -> Optional[EngineSession]:
        """按 ID 返回已存在的会话。"""

        return self._sessions.get(session_id)

    async def cleanup_idle(self, timeout: timedelta = timedelta(minutes=30)) -> None:
        """关闭超时未活跃的会话并释放资源。"""

        now = datetime.now(timezone.utc)
        stale_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.last_active > timeout
        ]

        for session_id in stale_ids:
            session = self._sessions.pop(session_id, None)
            if session is not None:
                session.close()

    async def close_all(self) -> None:
        """关闭所有会话，供服务停止时调用。"""

        for session in list(self._sessions.values()):
            session.close()

        self._sessions.clear()
