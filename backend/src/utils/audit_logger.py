"""审计日志系统

修复P3-2: 添加结构化的审计日志，用于安全监控和故障排查
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import traceback


class AuditEventType(Enum):
    """审计事件类型"""
    # 用户行为
    USER_REQUEST = "user_request"
    USER_INPUT = "user_input"

    # 系统事件
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"

    # 安全事件
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    AUTH_FAILURE = "auth_failure"

    # 性能事件
    SLOW_QUERY = "slow_query"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"

    # 错误事件
    EXCEPTION = "exception"
    VALIDATION_ERROR = "validation_error"


class AuditLogger:
    """审计日志记录器

    特性:
    - 结构化日志（JSON格式）
    - 自动添加时间戳和会话ID
    - 支持敏感数据脱敏
    - 可配置日志级别
    """

    def __init__(self, service_name: str = "gaokaoagent"):
        """初始化审计日志记录器

        Args:
            service_name: 服务名称
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"audit.{service_name}")

        # 配置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感数据

        Args:
            data: 原始数据

        Returns:
            脱敏后的数据
        """
        # 敏感字段列表
        sensitive_fields = {
            'password', 'token', 'api_key', 'secret',
            'authorization', 'cookie', 'session'
        }

        sanitized = {}
        for key, value in data.items():
            # 检查是否为敏感字段
            if any(s in key.lower() for s in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ):
        """记录审计事件

        Args:
            event_type: 事件类型
            user_id: 用户ID
            session_id: 会话ID
            ip_address: IP地址
            details: 事件详情
            level: 日志级别 (debug, info, warning, error, critical)
        """
        # 构建审计日志条目
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "event_type": event_type.value,
            "user_id": user_id or "anonymous",
            "session_id": session_id or "unknown",
            "ip_address": ip_address or "unknown",
        }

        # 添加详情（脱敏）
        if details:
            audit_entry["details"] = self._sanitize_data(details)

        # 转换为JSON字符串
        log_message = json.dumps(audit_entry, ensure_ascii=False)

        # 根据级别记录日志
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(log_message)

    def log_request(
        self,
        method: str,
        path: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """记录API请求

        Args:
            method: HTTP方法
            path: 请求路径
            ip_address: 客户端IP
            user_agent: User-Agent头
            session_id: 会话ID
        """
        self.log_event(
            event_type=AuditEventType.USER_REQUEST,
            ip_address=ip_address,
            session_id=session_id,
            details={
                "method": method,
                "path": path,
                "user_agent": user_agent
            }
        )

    def log_analysis(
        self,
        session_id: str,
        ip_address: str,
        score: Optional[int],
        rank: Optional[int],
        subject_group: Optional[str],
        success: bool,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        """记录分析请求

        Args:
            session_id: 会话ID
            ip_address: IP地址
            score: 高考分数
            rank: 位次
            subject_group: 选科组合
            success: 是否成功
            duration_ms: 耗时（毫秒）
            error: 错误信息
        """
        event_type = (
            AuditEventType.ANALYSIS_COMPLETE if success
            else AuditEventType.ANALYSIS_FAILED
        )

        details = {
            "score": score,
            "rank": rank,
            "subject_group": subject_group,
            "duration_ms": duration_ms
        }

        if error:
            details["error"] = error

        self.log_event(
            event_type=event_type,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
            level="info" if success else "error"
        )

    def log_rate_limit(
        self,
        ip_address: str,
        remaining_quota: int
    ):
        """记录速率限制事件

        Args:
            ip_address: IP地址
            remaining_quota: 剩余配额
        """
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            details={
                "remaining_quota": remaining_quota
            },
            level="warning"
        )

    def log_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """记录异常

        Args:
            exception: 异常对象
            context: 上下文信息
            session_id: 会话ID
            ip_address: IP地址
        """
        details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc()
        }

        if context:
            details["context"] = context

        self.log_event(
            event_type=AuditEventType.EXCEPTION,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
            level="error"
        )

    def log_cache_event(
        self,
        cache_key: str,
        hit: bool,
        session_id: Optional[str] = None
    ):
        """记录缓存事件

        Args:
            cache_key: 缓存键
            hit: 是否命中
            session_id: 会话ID
        """
        event_type = AuditEventType.CACHE_HIT if hit else AuditEventType.CACHE_MISS

        self.log_event(
            event_type=event_type,
            session_id=session_id,
            details={"cache_key": cache_key},
            level="debug"
        )


# 全局审计日志实例
audit_logger = AuditLogger()
