"""HTTP 安全头部中间件"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    添加安全 HTTP 头部以增强应用防御能力
    
    包含的安全头部:
    - X-Content-Type-Options: 防止 MIME 类型嗅探
    - X-Frame-Options: 防止点击劫持
    - X-XSS-Protection: 启用浏览器 XSS 保护
    - Content-Security-Policy: 内容安全策略
    """
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # 基本安全头部
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 内容安全策略（针对本地开发调整）
        # 允许 localhost 和 WebSocket 连接
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws://localhost:* http://localhost:* ws://127.0.0.1:* http://127.0.0.1:*; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        return response
