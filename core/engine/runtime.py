"""WASM 引擎运行时，实现 WASMRuntimeInterface。"""

# pyright: reportArgumentType=false, reportCallIssue=false

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import wasmtime

from core.interfaces import EngineHandleInterface, WASMRuntimeInterface

WASM_FILE_NAME = "llmnemeust_bg.wasm"


@dataclass
class EngineHandle(EngineHandleInterface):
    """封装单个 WASM Engine 实例的上下文。"""

    store: wasmtime.Store
    instance: wasmtime.Instance
    memory: wasmtime.Memory
    engine_ptr: int
    engine_process: wasmtime.Func
    engine_tick: wasmtime.Func
    malloc: wasmtime.Func
    free: wasmtime.Func
    drop: wasmtime.Func

    def close(self) -> None:
        """显式释放引擎实例。"""
        if self.engine_ptr != 0:
            # wasm-bindgen 生成的 free 方法第二个参数恒为 1
            self.drop(self.store, self.engine_ptr, 1)
            self.engine_ptr = 0


class WASMRuntime(WASMRuntimeInterface):
    """基于 wasmtime 的 WASM 引擎运行时。"""

    def __init__(self, wasm_path: Optional[str | Path] = None) -> None:
        self._wasm_path = self._resolve_wasm_path(wasm_path)
        self._engine = wasmtime.Engine()
        self._module = wasmtime.Module.from_file(self._engine, str(self._wasm_path))

    def create_engine(self, config_json: str) -> EngineHandle:
        """加载 WASM 模块并创建 Engine 实例。"""
        store = wasmtime.Store(self._engine)
        memory_ref: list[Optional[wasmtime.Memory]] = [None]

        def _host_throw(ptr: int, length: int) -> None:
            """处理 WASM 侧抛出的异常。"""
            message = "WASM 执行异常"
            memory = memory_ref[0]
            if memory is not None:
                try:
                    message = self._read_utf8(memory, store, ptr, length)
                except Exception:
                    message = f"{message}（无法读取异常信息）"
            raise RuntimeError(message)

        def _init_externref_table() -> None:
            """wasm-bindgen 外部引用初始化，当前无需额外处理。"""
            return None

        imports = [
            wasmtime.Func(
                store,
                wasmtime.FuncType(
                    [wasmtime.ValType.i32(), wasmtime.ValType.i32()], []
                ),
                _host_throw,
            ),
            wasmtime.Func(
                store, wasmtime.FuncType([], []), _init_externref_table
            ),
        ]

        instance = wasmtime.Instance(store, self._module, imports)
        exports = instance.exports(store)

        memory = exports["memory"]
        memory_ref[0] = memory

        engine_new = exports["engine_new"]
        engine_process = exports["engine_process"]
        engine_tick = exports["engine_tick"]
        malloc = exports["__wbindgen_malloc"]
        free = exports["__wbindgen_free"]
        drop = exports["__wbg_engine_free"]

        config_ptr, config_len = self._write_utf8(memory, store, malloc, config_json)
        engine_ptr = engine_new(store, config_ptr, config_len)

        return EngineHandle(
            store=store,
            instance=instance,
            memory=memory,
            engine_ptr=engine_ptr,
            engine_process=engine_process,
            engine_tick=engine_tick,
            malloc=malloc,
            free=free,
            drop=drop,
        )

    def process(self, handle: EngineHandleInterface, input_json: str) -> List[str]:
        """调用引擎的 process 方法并返回 JSON Lines 列表。"""
        engine_handle = self._ensure_handle(handle)
        input_ptr, input_len = self._write_utf8(
            engine_handle.memory, engine_handle.store, engine_handle.malloc, input_json
        )

        result_ptr, result_len = self._unwrap_pair(
            engine_handle.engine_process(
                engine_handle.store, engine_handle.engine_ptr, input_ptr, input_len
            )
        )

        return self._consume_lines(engine_handle, result_ptr, result_len)

    def tick(self, handle: EngineHandleInterface, elapsed_ms: int) -> List[str]:
        """调用引擎的 tick 方法并返回 JSON Lines 列表。"""
        engine_handle = self._ensure_handle(handle)

        result_ptr, result_len = self._unwrap_pair(
            engine_handle.engine_tick(
                engine_handle.store, engine_handle.engine_ptr, int(elapsed_ms)
            )
        )

        return self._consume_lines(engine_handle, result_ptr, result_len)

    def _consume_lines(
        self, handle: EngineHandle, result_ptr: int, result_len: int
    ) -> List[str]:
        """读取 WASM 返回的字符串并拆分为行。"""
        memory = handle.memory
        store = handle.store
        try:
            output = self._read_utf8(memory, store, result_ptr, result_len)
        finally:
            # wasm-bindgen 返回的字符串由宿主负责释放，按惯例对齐参数传 1
            handle.free(store, result_ptr, result_len, 1)

        return [line for line in output.splitlines() if line]

    def _read_utf8(
        self, memory: wasmtime.Memory, store: wasmtime.Store, ptr: int, length: int
    ) -> str:
        """从 WASM 线性内存中读取 UTF-8 字符串。"""
        if length == 0:
            return ""

        total_len = memory.data_len(store)
        if ptr < 0 or ptr + length > total_len:
            raise MemoryError("WASM 内存读取越界")

        raw_ptr = memory.data_ptr(store)
        addr = ctypes.addressof(raw_ptr.contents) + ptr
        data = ctypes.string_at(addr, length)
        return data.decode("utf-8")

    def _write_utf8(
        self,
        memory: wasmtime.Memory,
        store: wasmtime.Store,
        malloc_fn: wasmtime.Func,
        text: str,
    ) -> tuple[int, int]:
        """编码字符串并写入 WASM 内存，返回指针与长度。"""
        encoded = text.encode("utf-8")
        length = len(encoded)
        ptr = malloc_fn(store, length, 1)

        if length:
            total_len = memory.data_len(store)
            if ptr < 0 or ptr + length > total_len:
                raise MemoryError("WASM 内存写入越界")
            raw_ptr = memory.data_ptr(store)
            dest = ctypes.addressof(raw_ptr.contents) + ptr
            ctypes.memmove(dest, encoded, length)

        return ptr, length

    def _unwrap_pair(self, result: object) -> tuple[int, int]:
        """将多返回值包装为 (ptr, len)。"""
        if isinstance(result, (list, tuple)) and len(result) == 2:
            return int(result[0]), int(result[1])
        raise RuntimeError("WASM 返回值格式不正确，期望包含两个元素")

    def _ensure_handle(self, handle: EngineHandleInterface) -> EngineHandle:
        """校验句柄类型并向下转换。"""
        if not isinstance(handle, EngineHandle):
            raise TypeError("handle 必须由 WASMRuntime.create_engine 创建")
        if handle.engine_ptr == 0:
            raise RuntimeError("引擎实例已释放或未初始化")
        return handle

    def _resolve_wasm_path(self, custom_path: Optional[str | Path]) -> Path:
        """解析 WASM 文件路径，优先使用自定义路径。"""
        if custom_path:
            path = Path(custom_path).expanduser()
        else:
            path = Path(__file__).resolve().parents[2] / "wasm" / WASM_FILE_NAME

        if not path.exists():
            raise FileNotFoundError(f"未找到 WASM 文件: {path}")
        return path
