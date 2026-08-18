"""
T6-Q4 可导入版 LLM 网关（Q2 逻辑工程化：配置注入 + JSON 日志 + 可测试）
"""
import asyncio
import logging
import random

from config import GatewayConfig
from jsonlog import get_logger, log_with

logger = get_logger("llm.gateway")


class ApiError(Exception):
    pass


async def mock_llm_api(task_id, delay=0.05, fail_rate=0.0, rng=None,
                       fail_ids=frozenset(), _attempts={}):
    """fail_ids 里的任务仅首调失败（重试可救）；_attempts 记调用次数"""
    rng = rng or random.Random()
    await asyncio.sleep(delay)
    n = _attempts.get(task_id, 0)
    _attempts[task_id] = n + 1
    if (task_id in fail_ids and n == 0) or rng.random() < fail_rate:
        raise ApiError(f"task-{task_id} 服务端 500")
    return f"resp-{task_id}"


async def call_with_gateway(task_ids, config: GatewayConfig, api=mock_llm_api,
                            delay=0.05, fail_ids=frozenset(), seed=42):
    """限流 + 退避重试 + 超时 + TaskGroup 结构化取消；api 可注入便于测试"""
    rng = random.Random(seed)
    sem = asyncio.Semaphore(config.concurrency)

    async def one_call(task_id):
        async with sem:
            for attempt in range(config.max_retries + 1):
                try:
                    async with asyncio.timeout(config.per_call_timeout):
                        result = await api(task_id, delay=delay,
                                           fail_rate=0.0, rng=rng,
                                           fail_ids=fail_ids)
                    log_with(logger, logging.INFO, "call_ok",
                             task_id=task_id, attempt=attempt)
                    return result
                except ApiError:
                    if attempt == config.max_retries:
                        log_with(logger, logging.ERROR, "call_failed",
                                 task_id=task_id, attempts=attempt + 1)
                        raise
                    backoff = 0.01 * (2 ** attempt) * (0.5 + rng.random())
                    log_with(logger, logging.WARNING, "retry_scheduled",
                             task_id=task_id, attempt=attempt,
                             backoff_ms=round(backoff * 1000, 1))
                    await asyncio.sleep(backoff)

    async with asyncio.TaskGroup() as tg:
        tasks = {tid: tg.create_task(one_call(tid)) for tid in task_ids}
    return {tid: t.result() for tid, t in tasks.items()}


async def streaming_pipeline(tokens_producer, maxsize=3, consume_delay=0.02):
    """Q3 背压管道的可导入版：返回 (收到数, 生产端挂起次数)"""
    q = asyncio.Queue(maxsize=maxsize)
    blocked = 0
    import time

    async def producer():
        nonlocal blocked
        async for tok in tokens_producer:
            t0 = time.perf_counter()
            await q.put(tok)
            if time.perf_counter() - t0 > 0.005:
                blocked += 1
        await q.put(None)                              # 哨兵：流结束

    async def consumer():
        got = 0
        while True:
            tok = await q.get()
            if tok is None:
                break
            await asyncio.sleep(consume_delay)
            got += 1
        return got

    prod = asyncio.create_task(producer())
    got = await consumer()
    await prod
    return got, blocked
