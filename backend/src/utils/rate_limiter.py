"""简单的内存速率限制器"""
import time
from collections import defaultdict
from typing import Dict, Tuple
import threading


class RateLimiter:
    """简单的基于令牌桶的速率限制器"""

    def __init__(self, requests_per_minute: int = 10):
        """
        Args:
            requests_per_minute: 每分钟允许的请求数
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 60秒窗口
        # 存储: {ip: [(timestamp1, timestamp2, ...)]}
        self.request_log: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        检查是否允许请求

        Args:
            client_id: 客户端ID（通常是IP地址）

        Returns:
            (是否允许, 剩余配额)
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_size

            # 清理过期记录
            self.request_log[client_id] = [
                ts for ts in self.request_log[client_id]
                if ts > cutoff_time
            ]

            # 检查是否超过限制
            recent_requests = len(self.request_log[client_id])
            if recent_requests >= self.requests_per_minute:
                remaining = 0
                return False, remaining

            # 记录本次请求
            self.request_log[client_id].append(current_time)
            remaining = self.requests_per_minute - recent_requests - 1
            return True, remaining

    def cleanup(self):
        """清理过期记录"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_size

            # 清理所有过期记录
            for client_id in list(self.request_log.keys()):
                self.request_log[client_id] = [
                    ts for ts in self.request_log[client_id]
                    if ts > cutoff_time
                ]

                # 删除空记录
                if not self.request_log[client_id]:
                    del self.request_log[client_id]
