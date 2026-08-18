"""
T6-Q4 演示入口：JSON 结构化日志实跑 + 配置 fail fast 实测
运行：.venv/bin/python 代码/T6/Q4-工程化/demo.py
"""
import asyncio
import os
import sys

from config import ConfigError, GatewayConfig
from gateway import call_with_gateway, mock_llm_api
from jsonlog import get_logger, log_with
import logging

logger = get_logger("llm.demo")


async def main():
    # ① fail fast 实测：缺 LLM_API_KEY 直接炸
    try:
        GatewayConfig.from_env(env={})
        print("不该走到这")
    except ConfigError as e:
        log_with(logger, logging.ERROR, "config_rejected", reason=str(e))

    # ② 正常路径：env 注入配置；fail_ids 强制 t1/t3 首调失败走重试，
    # 全程 JSON 日志（retry_scheduled/call_ok 字段可观测）
    env = {"LLM_API_KEY": "sk-demo", "LLM_GATEWAY_CONCURRENCY": "4"}
    cfg = GatewayConfig.from_env(env=env)
    log_with(logger, logging.INFO, "config_loaded", **{
        "concurrency": cfg.concurrency, "timeout": cfg.per_call_timeout,
        "endpoint": cfg.endpoint,
    })
    results = await call_with_gateway([f"t{i}" for i in range(8)], cfg,
                                      api=mock_llm_api, delay=0.05,
                                      fail_ids=frozenset({"t1", "t3"}), seed=42)
    log_with(logger, logging.INFO, "batch_done", count=len(results))


if __name__ == "__main__":
    asyncio.run(main())
