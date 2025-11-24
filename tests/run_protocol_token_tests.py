"""
综合测试：CompactProtocol、TokenTracker 以及 websocket 集成路径。

执行方式：
  python -m tests.run_protocol_token_tests

输出：
  - 各测试项通过/失败
  - 发现的问题与细节
  - 基准性能（耗时）与内存峰值
"""

from __future__ import annotations

import asyncio
import json
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from api.protocol import CompactProtocol
from core.monitor.token_tracker import TokenTracker
from api.websocket import handle_conversation_request


# ============ 通用辅助 ============

@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str = ""


class TestReport:
    def __init__(self) -> None:
        self.items: List[CaseResult] = []
        self.problems: List[str] = []
        self.performance: Dict[str, Any] = {}

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.items.append(CaseResult(name=name, ok=ok, detail=detail))
        if not ok:
            self.problems.append(f"[Fail] {name}: {detail}")

    def summary(self) -> Dict[str, Any]:
        total = len(self.items)
        passed = sum(1 for i in self.items if i.ok)
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
        }


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


# ============ 单元测试：CompactProtocol ============

def test_protocol_parse_and_compact(report: TestReport) -> None:
    # 标准消息（长字段）
    standard = {
        "id": "1",
        "type": "conversation_request",
        "timestamp": "2025-11-17T12:00:00Z",
        "playerName": "Steve",
        "companionName": "AICompanion",
        "message": "Hello 世界",
        "extra": {"foo": 123},
    }

    compact = CompactProtocol.compact(standard)
    parsed = CompactProtocol.parse(compact)

    try:
        _assert(parsed.get("type") == "conversation_request", "type 展开错误")
        _assert(parsed.get("message") == standard["message"], "message 不一致")
        _assert(parsed.get("playerName") == standard["playerName"], "playerName 不一致")
        _assert(parsed.get("companionName") == standard["companionName"], "companionName 不一致")
        _assert(parsed.get("extra") == {"foo": 123}, "未知字段透传失败")

        # 再次压缩应得到短键与短类型
        compact2 = CompactProtocol.compact(parsed)
        _assert(compact2.get("t") == "cs" or compact2.get("t") == "cr", "type 压缩未使用短码")
        _assert(compact2.get("m") == "Hello 世界", "短键 m 缺失或值错误")

        report.add("协议-标准↔紧凑-往返", True)
    except AssertionError as e:
        report.add("协议-标准↔紧凑-往返", False, str(e))


def test_protocol_backward_compat(report: TestReport) -> None:
    # 旧版 data 结构 + 短类型
    legacy = {
        "type": "cr",
        "data": {
            "player_name": "Alex",
            "msg": "嗨",
            "companion": "Bot",
            "hp": 9,
        },
    }
    parsed = CompactProtocol.parse(legacy)

    try:
        _assert(parsed.get("type") == "conversation_request", "旧版 type 未正确展开")
        _assert(parsed.get("playerName") == "Alex", "player_name → playerName 失败")
        _assert(parsed.get("message") == "嗨", "msg → message 失败")
        _assert(parsed.get("companionName") == "Bot", "companion → companionName 失败")
        _assert(parsed.get("health") == 9, "hp → health 失败")
        report.add("协议-向后兼容(data)", True)
    except AssertionError as e:
        report.add("协议-向后兼容(data)", False, str(e))


def test_protocol_edge_cases(report: TestReport) -> None:
    # 空对象
    try:
        _assert(CompactProtocol.parse({}) == {}, "空对象 parse 应返回空字典")
        _assert(CompactProtocol.compact({}) == {}, "空对象 compact 应返回空字典")
    except AssertionError as e:
        report.add("协议-空消息", False, str(e))
    else:
        report.add("协议-空消息", True)

    # 混合键名与未知字段
    mixed = {
        "t": "cr",
        "type": "conversation_request",  # 冲突：长短并存，期望以长覆盖
        "m": "hi",
        "xyz": 7,
        "data": {"player": "P1"},
    }
    parsed = CompactProtocol.parse(mixed)
    try:
        _assert(parsed.get("type") == "conversation_request", "长/短 type 冲突处理失败")
        _assert(parsed.get("message") == "hi", "短键 m 未展开为 message")
        _assert(parsed.get("playerName") == "P1", "data.player → playerName 失败")
        _assert(parsed.get("xyz") == 7, "未知字段应透传")
        report.add("协议-混合键与未知字段", True)
    except AssertionError as e:
        report.add("协议-混合键与未知字段", False, str(e))


def test_routing_type_detection(report: TestReport) -> None:
    # 仅紧凑顶层短键（无长 type）
    compact_only = {"t": "cr", "m": "hi", "p": "Alex"}
    norm = CompactProtocol.parse(compact_only)
    # 旧版 data 格式
    legacy = {"type": "cr", "data": {"player": "A", "msg": "yo"}}
    norm2 = CompactProtocol.parse(legacy)

    try:
        _assert(norm.get("type") == "conversation_request", "紧凑短码未展开为长类型")
        _assert(norm2.get("type") == "conversation_request", "旧版 data 类型展开失败")
        report.add("协议-路由类型检测", True)
    except AssertionError as e:
        report.add("协议-路由类型检测", False, str(e))


# ============ 单元测试：TokenTracker ============

def test_token_tracker_basic(report: TestReport) -> None:
    std = {
        "id": "1",
        "type": "conversation_response",
        "companionName": "AICompanion",
        "message": "你好，世界！Hello World!",
    }
    cpt = CompactProtocol.compact(std)
    stats = TokenTracker.compare(std, cpt)

    try:
        # 自洽性：结果字段存在且数值非负
        for key in ["standard_tokens", "compact_tokens", "saved_tokens", "saved_percent"]:
            _assert(key in stats, f"统计缺少字段 {key}")
        _assert(stats["standard_tokens"] >= 0 and stats["compact_tokens"] >= 0, "token 计数应为非负")
        _assert(stats["standard_tokens"] >= stats["compact_tokens"], "紧凑格式理论上应不大于标准格式")
        report.add("TokenTracker-基础", True)
    except AssertionError as e:
        report.add("TokenTracker-基础", False, str(e))


def test_token_tracker_edge(report: TestReport) -> None:
    std = {"type": "conversation_response", "message": ""}
    cpt = CompactProtocol.compact(std)
    stats = TokenTracker.compare(std, cpt)

    try:
        _assert(stats["standard_tokens"] >= 0, "空消息 token 不应为负")
        _assert(stats["saved_percent"] >= 0, "节省百分比不应为负")
        report.add("TokenTracker-空消息", True)
    except AssertionError as e:
        report.add("TokenTracker-空消息", False, str(e))


# ============ 集成测试：websocket.handle_conversation_request ============

class DummyWS:
    """最小可用的 WebSocket 假对象，用于捕获 send_json。"""

    def __init__(self) -> None:
        self.sent: List[Any] = []

    async def send_json(self, payload: Any) -> None:
        self.sent.append(payload)


async def _test_ws_conversation_flow(report: TestReport) -> None:
    ws = DummyWS()
    msg = {
        # 注意：外层路由根据长类型判断，这里直接调用 handler，因此允许短或长
        "type": "conversation_request",
        "p": "Steve",  # 即便传了短键，parse 也应展开
        "m": "请复述这句话",
    }

    preview = await handle_conversation_request(ws, msg, client_id="test-client")
    try:
        _assert(preview is not None, "handler 未返回预览字符串")
        _assert(len(ws.sent) == 1, "未捕获到发送数据")
        payload = ws.sent[0]
        # 期望为紧凑格式，类型短码 cs
        _assert(payload.get("t") == "cs", "响应类型应为 cs")
        _assert("[Echo] 收到：" in payload.get("m", ""), "响应内容未包含 Echo 前缀")
        report.add("WS-对话请求-集成", True)
    except AssertionError as e:
        report.add("WS-对话请求-集成", False, str(e))


# ============ 基准测试（性能/内存） ============

def bench_parse_compact(report: TestReport) -> None:
    base = {
        "id": "42",
        "type": "conversation_request",
        "timestamp": "2025-11-17T12:00:00Z",
        "playerName": "Alex",
        "companionName": "AICompanion",
        "message": "你好" * 20 + " Hello" * 20,
        "position": {"x": 12, "y": 64, "z": -20},
        "health": 18,
        "extra": {"foo": 1, "bar": "baz"},
    }

    loops = 20000  # 2 万次，兼顾速度与稳定性

    compact = CompactProtocol.compact(base)

    tracemalloc.start()
    t0 = time.perf_counter()
    for _ in range(loops):
        _ = CompactProtocol.parse(compact)
    t1 = time.perf_counter()
    current, peak1 = tracemalloc.get_traced_memory()

    # 紧接着压缩基准
    t2 = time.perf_counter()
    for _ in range(loops):
        _ = CompactProtocol.compact(base)
    t3 = time.perf_counter()
    current2, peak2 = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report.performance["parse_us_per_op"] = round((t1 - t0) / loops * 1e6, 2)
    report.performance["compact_us_per_op"] = round((t3 - t2) / loops * 1e6, 2)
    report.performance["parse_peak_kb"] = round(peak1 / 1024, 1)
    report.performance["compact_peak_kb"] = round(peak2 / 1024, 1)


def bench_token_compare(report: TestReport) -> None:
    standard = {
        "id": "99",
        "type": "conversation_response",
        "companionName": "AICompanion",
        "message": ("你好世界" * 50) + ("HelloWorld" * 50),
    }
    compact = CompactProtocol.compact(standard)

    loops = 10000
    tracemalloc.start()
    t0 = time.perf_counter()
    for _ in range(loops):
        _ = TokenTracker.compare(standard, compact)
    t1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report.performance["token_compare_us_per_op"] = round((t1 - t0) / loops * 1e6, 2)
    report.performance["token_compare_peak_kb"] = round(peak / 1024, 1)


# ============ runner ============

def run() -> TestReport:
    report = TestReport()

    # 协议转换
    test_protocol_parse_and_compact(report)
    test_protocol_backward_compat(report)
    test_protocol_edge_cases(report)
    test_routing_type_detection(report)

    # Token 统计
    test_token_tracker_basic(report)
    test_token_tracker_edge(report)

    # 集成（异步）
    asyncio.run(_test_ws_conversation_flow(report))

    # 基准
    bench_parse_compact(report)
    bench_token_compare(report)

    return report


def _fmt_line(ok: bool, name: str, detail: str) -> str:
    status = "通过" if ok else "失败"
    return f"[ {status} ] {name}" + (f" → {detail}" if detail else "")


if __name__ == "__main__":
    r = run()
    # 概览
    s = r.summary()
    print("=" * 64)
    print("测试汇总：")
    print(json.dumps(s, ensure_ascii=False, indent=2))

    # 明细
    print("-" * 64)
    print("用例结果：")
    for item in r.items:
        print(_fmt_line(item.ok, item.name, item.detail))

    # 性能
    print("-" * 64)
    print("性能与内存：")
    print(json.dumps(r.performance, ensure_ascii=False, indent=2))

    # 问题
    print("-" * 64)
    print("发现的问题：")
    if not r.problems:
        print("无")
    else:
        for p in r.problems:
            print(p)
