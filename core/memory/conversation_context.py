"""基于玩家的会话上下文管理。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, TypedDict
import logging

logger = logging.getLogger("core.memory.conversation_context")


class ConversationMessage(TypedDict):
    """会话消息结构。"""

    role: str
    content: str
    timestamp: datetime


@dataclass(slots=True)
class ConversationSession:
    """玩家会话，存储消息历史。"""

    player_name: str
    started_at: datetime
    messages: List[ConversationMessage] = field(default_factory=list)


class ConversationContext:
    """管理多玩家对话上下文。"""

    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = RLock()

    def create_session(self, client_id: str, player_name: str) -> ConversationSession:
        """创建/覆盖指定客户端的会话。"""

        with self._lock:
            session = ConversationSession(
                player_name=player_name,
                started_at=datetime.now(timezone.utc),
            )
            self._sessions[client_id] = session
            logger.info("创建对话会话: client=%s, player=%s", client_id, player_name)
            return session

    def has_session(self, client_id: str) -> bool:
        """判断客户端是否存在会话。"""

        with self._lock:
            return client_id in self._sessions

    def add_message(self, client_id: str, role: str, content: str, player_name: str | None = None) -> None:
        """向会话追加消息，必要时自动创建会话。"""

        with self._lock:
            session = self._sessions.get(client_id)
            if session is None:
                session = ConversationSession(
                    player_name=player_name or "玩家",
                    started_at=datetime.now(timezone.utc),
                )
                self._sessions[client_id] = session
                logger.warning("追加消息时会话不存在，已自动创建: client=%s", client_id)

            session.messages.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc),
                }
            )
            logger.debug(
                "记录会话消息: client=%s, role=%s, len=%s", client_id, role, len(session.messages)
            )

    def get_history(self, client_id: str) -> List[ConversationMessage]:
        """返回指定客户端的全部历史。"""

        with self._lock:
            session = self._sessions.get(client_id)
            if session is None:
                return []
            return list(session.messages)

    def clear_session(self, client_id: str) -> None:
        """清理指定客户端会话。"""

        with self._lock:
            if client_id in self._sessions:
                del self._sessions[client_id]
                logger.info("清除对话会话: client=%s", client_id)
            else:
                logger.debug("尝试清除不存在的会话: client=%s", client_id)
