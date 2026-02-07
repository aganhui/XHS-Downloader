"""
请求日志记录模块
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# 日志文件路径
LOG_DIR = Path(os.getenv("XHS_LOG_DIR", "/tmp/xhs_logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "request_logs.jsonl"


def log_request(
    endpoint: str,
    request_data: Dict[str, Any],
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
):
    """
    记录API请求日志

    Args:
        endpoint: API端点路径
        request_data: 请求数据
        response_data: 响应数据（成功时）
        error: 错误信息（失败时）
        duration_ms: 请求耗时（毫秒）
    """
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "endpoint": endpoint,
            "request": request_data,
            "response": response_data,
            "error": error,
            "duration_ms": duration_ms,
            "success": error is None,
        }

        # 追加到JSONL文件
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # 日志记录失败不应该影响主流程
        print(f"Failed to log request: {e}")


def get_logs(limit: int = 100, offset: int = 0) -> tuple[list[Dict[str, Any]], int]:
    """
    获取日志记录

    Args:
        limit: 返回的最大记录数
        offset: 跳过的记录数

    Returns:
        (日志列表, 总记录数)
    """
    if not LOG_FILE.exists():
        return [], 0

    try:
        logs = []
        # 读取所有日志行
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)

        # 从后往前读取（最新的在前）
        for line in reversed(lines[offset:offset + limit]):
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                continue

        return logs, total
    except Exception as e:
        print(f"Failed to read logs: {e}")
        return [], 0


def clear_logs():
    """清空日志文件"""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        return True
    except Exception as e:
        print(f"Failed to clear logs: {e}")
        return False
