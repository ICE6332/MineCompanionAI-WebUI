"""连接状态追踪。"""

from __future__ import annotations

from datetime import datetime, timezone

from models.monitor import ConnectionStatus


class ConnectionTracker:
    """仅负责连接状态的读写。"""

    def __init__(self) -> None:
        self._status = ConnectionStatus()

    def set_mod_connected(self, client_id: str) -> None:
        self._status.mod_client_id = client_id
        self._status.mod_connected_at = datetime.now(timezone.utc)

    def set_mod_disconnected(self) -> None:
        self._status.mod_client_id = None
        self._status.mod_connected_at = None

    def update_mod_last_message(self) -> None:
        self._status.mod_last_message_at = datetime.now(timezone.utc)

    def set_llm_status(self, provider: str, ready: bool) -> None:
        self._status.llm_provider = provider
        self._status.llm_ready = ready

    def get_status(self) -> ConnectionStatus:
        return self._status
