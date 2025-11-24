"""紧凑 JSON 协议解析与压缩工具。

该模块提供 ``CompactProtocol``，用于在“紧凑格式(短字段)”与“内部标准格式(长字段)”之间转换，
并保持向后兼容：同时支持旧版包含 ``data`` 字段的标准消息结构。
"""

from typing import Any, Dict


class CompactProtocol:
    """紧凑协议编解码器。

    - parse: 将紧凑格式/旧版标准格式解析为内部标准格式（展字段名与类型）。
    - compact: 将内部标准格式压缩为紧凑格式（短字段名与短类型）。
    """

    # 字段映射表（短 → 长）
    SHORT_TO_LONG: Dict[str, str] = {
        "i": "id",
        "t": "type",
        "ts": "timestamp",
        "p": "playerName",
        "c": "companionName",
        "m": "message",
        "a": "action",
        "pos": "position",
        "hp": "health",
    }

    # 类型映射表（短 → 长）
    TYPE_MAP: Dict[str, str] = {
        "cr": "conversation_request",
        "cs": "conversation_response",
        "gs": "game_state_update",
        "ac": "action_command",
        "er": "error",
    }

    _LONG_TO_SHORT: Dict[str, str] = {v: k for k, v in SHORT_TO_LONG.items()}
    _TYPE_LONG_TO_SHORT: Dict[str, str] = {v: k for k, v in TYPE_MAP.items()}

    # 字段别名映射（长/蛇形/简写 → 标准长字段名）
    FIELD_ALIASES: Dict[str, str] = {
        "playerName": "playerName",
        "player_name": "playerName",
        "player": "playerName",
        "message": "message",
        "msg": "message",
        "companionName": "companionName",
        "companion_name": "companionName",
        "companion": "companionName",
        "action": "action",
        "position": "position",
        "pos": "position",
        "health": "health",
        "hp": "health",
        "id": "id",
        "timestamp": "timestamp",
        "type": "type",
    }

    @classmethod
    def _expand_type(cls, value: Any) -> Any:
        """将类型值从短码展开为长字符串；若已为长字符串则原样返回。"""
        if isinstance(value, str) and value in cls.TYPE_MAP:
            return cls.TYPE_MAP[value]
        return value

    @classmethod
    def _compact_type(cls, value: Any) -> Any:
        """将类型值从长字符串压缩为短码；若无对应短码则原样返回。"""
        if isinstance(value, str) and value in cls._TYPE_LONG_TO_SHORT:
            return cls._TYPE_LONG_TO_SHORT[value]
        return value

    @classmethod
    def parse(cls, compact_msg: Dict[str, Any]) -> Dict[str, Any]:
        """紧凑格式 → 内部标准格式。

        兼容输入：
        - 紧凑格式（短字段：如 ``t``、``m`` 等）；
        - 新标准格式（长字段：如 ``type``、``message`` 等）；
        - 旧版标准格式（顶层包含 ``data``，内部键名如 ``player_name``、``player``）。

        返回：展开后的标准格式字典（顶层长字段，无 ``data`` 嵌套）。
        """
        if not isinstance(compact_msg, dict):
            raise ValueError("parse 期望 dict 输入")

        src: Dict[str, Any] = dict(compact_msg)
        result: Dict[str, Any] = {}

        def _normalize_key(key: str) -> str:
            if key in cls.SHORT_TO_LONG:
                return cls.SHORT_TO_LONG[key]
            if key in cls.FIELD_ALIASES:
                return cls.FIELD_ALIASES[key]
            return key

        def _assign(long_key: str, raw_value: Any) -> None:
            if long_key == "type":
                result[long_key] = cls._expand_type(raw_value)
            else:
                result[long_key] = raw_value

        # 1) 处理旧版 data 嵌套，优先填充基础字段
        data_obj = src.get("data")
        if isinstance(data_obj, dict):
            for key, value in data_obj.items():
                long_key = _normalize_key(key)
                _assign(long_key, value)

        # 2) 覆盖/补充顶层字段（紧凑键、长键、别名均可）
        for key, value in src.items():
            if key == "data":
                continue
            long_key = _normalize_key(key)
            _assign(long_key, value)

        # 3) 确保 type 已展开（兜底处理短码）
        if "type" in result:
            result["type"] = cls._expand_type(result["type"])

        return result

    @classmethod
    def compact(cls, standard_msg: Dict[str, Any]) -> Dict[str, Any]:
        """内部标准格式 → 紧凑格式。

        要求输入为“顶层长字段，无 data 嵌套”的标准结构；
        未知字段将原样透传。
        """
        if not isinstance(standard_msg, dict):
            raise ValueError("compact 期望 dict 输入")

        dest: Dict[str, Any] = {}
        for key, value in standard_msg.items():
            if key == "type":
                dest_key = cls._LONG_TO_SHORT.get(key, key)
                dest[dest_key] = cls._compact_type(value)
                continue

            short_key = cls._LONG_TO_SHORT.get(key)
            if short_key is not None:
                dest[short_key] = value
            else:
                # 未知字段：保持原名避免数据丢失
                dest[key] = value

        return dest
