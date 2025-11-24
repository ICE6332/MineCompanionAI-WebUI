"""统计相关接口。"""

from fastapi import APIRouter

from core.dependencies import MetricsDep
from models.monitor import TokenTrendStats

router = APIRouter()


@router.get("/token-trend", response_model=TokenTrendStats)
async def get_token_trend(metrics: MetricsDep) -> TokenTrendStats:
    """获取最近 24 小时的 token 消耗趋势。"""
    return metrics.get_token_trend()


@router.post("/token-trend/test")
async def inject_test_tokens(metrics: MetricsDep, tokens: int = 100) -> dict:
    """测试用：注入指定数量的 token 到当前小时统计。"""
    metrics.record_token_usage(tokens)
    return {
        "status": "ok",
        "tokens_added": tokens,
        "message": f"已添加 {tokens} tokens 到当前小时统计",
    }
