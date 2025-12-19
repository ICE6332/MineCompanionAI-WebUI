"""测试 WASM 运行时加载与调用"""

import pytest
from pathlib import Path
import orjson
from core.engine.runtime import WASMRuntime, EngineHandle


class TestWASMRuntime:
    @pytest.fixture
    def runtime(self):
        """创建 WASMRuntime 实例"""
        return WASMRuntime()

    @pytest.fixture
    def simple_config(self):
        """简单的引擎配置"""
        return {
            "character": {"id": "test_char", "name": "测试角色"},
            "vision": {},
            "story": [],
        }

    def test_load_wasm_module(self, runtime):
        """V1: 验证 WASM 模块能正确加载"""
        wasm_path = Path(__file__).resolve().parents[3] / "wasm" / "llmnemeust_bg.wasm"
        assert wasm_path.exists(), f"WASM 文件不存在: {wasm_path}"
        # runtime 初始化时已加载模块，验证无异常即可
        assert runtime._module is not None

    def test_create_engine(self, runtime, simple_config):
        """V1: 验证能创建 Engine 实例"""
        config_json = orjson.dumps(simple_config).decode("utf-8")
        handle = runtime.create_engine(config_json)

        assert isinstance(handle, EngineHandle)
        assert handle.engine_ptr != 0
        assert handle.memory is not None

        # 清理
        handle.close()

    def test_process_returns_json_lines(self, runtime, simple_config):
        """V1: 验证 process() 返回 JSON Lines 格式"""
        config_json = orjson.dumps(simple_config).decode("utf-8")
        handle = runtime.create_engine(config_json)

        try:
            input_event = {"type": "world_diff", "tick": 100, "diff": {"entities": []}}
            input_json = orjson.dumps(input_event).decode("utf-8")

            outputs = runtime.process(handle, input_json)

            assert isinstance(outputs, list)
            # 验证每一行都是有效 JSON
            for line in outputs:
                parsed = orjson.loads(line)
                assert isinstance(parsed, dict)
        finally:
            handle.close()

    def test_tick_method(self, runtime, simple_config):
        """V1: 验证 tick() 方法调用"""
        config_json = orjson.dumps(simple_config).decode("utf-8")
        handle = runtime.create_engine(config_json)

        try:
            outputs = runtime.tick(handle, elapsed_ms=16)
            assert isinstance(outputs, list)
            # tick 可能返回空列表（无超时事件）
        finally:
            handle.close()

    def test_engine_handle_close_idempotent(self, runtime, simple_config):
        """V1: 验证 EngineHandle.close() 幂等性"""
        config_json = orjson.dumps(simple_config).decode("utf-8")
        handle = runtime.create_engine(config_json)

        handle.close()
        assert handle.engine_ptr == 0

        # 再次调用不应报错
        handle.close()
        assert handle.engine_ptr == 0
