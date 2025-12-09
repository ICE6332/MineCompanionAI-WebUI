"""AI Engine 会话管理，实现单个引擎实例的生命周期控制。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import orjson

from core.engine.runtime import EngineHandle, WASMRuntime
from core.interfaces import EngineSessionInterface
from core.storage.story import StoryStore
from core.storage.vision import VisionStore


@dataclass(slots=True)
class EngineSession(EngineSessionInterface):
    """单个 AI Engine 会话，负责装配与驱动引擎实例。"""

    session_id: str
    character_id: str
    handle: Optional[EngineHandle] = None
    initialized: bool = False
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    async def initialize(
        self,
        runtime: WASMRuntime,
        vision_store: VisionStore,
        story_store: StoryStore,
        character_card: dict,
        config: dict,
    ) -> list[dict]:
        """初始化引擎：加载持久化状态并发送 Init。"""

        vision_snapshot = await vision_store.load(self.session_id) or {}
        story_history = await story_store.load_history(self.session_id)

        self.handle = runtime.create_engine(orjson.dumps(config).decode("utf-8"))

        init_payload = {
            "type": "init",
            "session_id": self.session_id,
            "character_card": character_card,
            "config": config,
            "vision": vision_snapshot,
            "story_history": story_history,
        }

        outputs = runtime.process(self.handle, orjson.dumps(init_payload).decode("utf-8"))
        self.initialized = True
        self.last_active = datetime.now(timezone.utc)

        return [orjson.loads(line) for line in outputs if line.strip()]

    async def on_world_diff(
        self,
        runtime: WASMRuntime,
        vision_store: VisionStore,
        story_store: StoryStore,
        diff: dict,
    ) -> list[dict]:
        """处理世界增量更新并回传可执行动作。"""

        if not self.initialized or self.handle is None:
            return [
                {
                    "type": "error",
                    "code": "not_initialized",
                    "message": "会话尚未初始化",
                }
            ]

        self.last_active = datetime.now(timezone.utc)

        event_payload = {
            "type": "event",
            "kind": "world_change",
            "data": diff,
        }

        outputs = runtime.process(self.handle, orjson.dumps(event_payload).decode("utf-8"))
        parsed = [orjson.loads(line) for line in outputs if line.strip()]

        vision_snapshot = diff.get("vision") if isinstance(diff, dict) else None
        tick_value = diff.get("tick") if isinstance(diff, dict) else None
        if vision_snapshot is not None:
            tick = tick_value
            if tick is None and isinstance(vision_snapshot, dict):
                tick = vision_snapshot.get("tick", 0)
            await vision_store.save(self.session_id, vision_snapshot, int(tick or 0))

        results: list[dict] = []
        for output in parsed:
            output_type = output.get("type")
            if output_type == "story_event":
                await story_store.append(self.session_id, output)
            if output_type in ("mod_action", "utterance"):
                results.append(output)

        return results

    async def on_player_message(
        self,
        runtime: WASMRuntime,
        player_id: str,
        text: str,
    ) -> list[dict]:
        """处理玩家文本输入。"""

        if not self.initialized or self.handle is None:
            return [
                {
                    "type": "error",
                    "code": "not_initialized",
                    "message": "会话尚未初始化",
                }
            ]

        self.last_active = datetime.now(timezone.utc)

        payload = {
            "type": "player_message",
            "player_id": player_id,
            "text": text,
        }

        outputs = runtime.process(self.handle, orjson.dumps(payload).decode("utf-8"))
        return [orjson.loads(line) for line in outputs if line.strip()]

    def close(self) -> None:
        """释放底层 WASM 资源。"""

        if self.handle is not None:
            self.handle.close()
            self.handle = None
