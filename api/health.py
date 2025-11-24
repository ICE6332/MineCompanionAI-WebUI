"""健康检查端点。"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from core.dependencies import LLMDep, MetricsDep
from core.interfaces import LLMServiceInterface, MetricsInterface

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/liveness")
async def liveness() -> dict:
    """存活探针：快速返回，供容器存活检测。"""
    return {"status": "ok"}


@router.get("/readiness")
async def readiness(metrics: MetricsDep, llm: LLMDep):
    """就绪探针：检查核心依赖状态。"""
    checks = {
        "websocket": _check_websocket(metrics),
        "llm": await _check_llm(llm),
    }
    all_healthy = all(item["status"] == "healthy" for item in checks.values())
    status_code = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks},
    )


def _check_websocket(metrics: MetricsInterface) -> dict:
    """检查 WebSocket 连接状态。"""
    conn_status = metrics.get_connection_status()
    return {
        "status": "healthy" if conn_status.mod_client_id else "degraded",
        "mod_connected": bool(conn_status.mod_client_id),
    }


async def _check_llm(llm: LLMServiceInterface) -> dict:
    """简易 LLM 探活，避免高成本调用。"""
    try:
        # 轻量级探测：只构造参数，不必强制调用外部服务
        wait_task = asyncio.sleep(0)  # 协程挂起确保接口兼容
        await wait_task
        has_key = bool(llm.config.get("api_key"))
        return {
            "status": "healthy" if has_key else "degraded",
            "api_key_present": has_key,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "unhealthy", "error": str(exc)}
