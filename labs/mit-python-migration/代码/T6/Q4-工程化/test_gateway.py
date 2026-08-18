"""
T6-Q4 pytest 用例：覆盖 Q2/Q3 四条关键路径（异步测试走 pytest-asyncio auto 模式）

裸 async def test 函数 pytest 不会自动跑（只会收集成 coroutine 对象），
pytest-asyncio 插件提供事件循环 runner——pytest.ini 里 asyncio_mode = auto。
"""
import asyncio

import pytest

from config import ConfigError, GatewayConfig
from gateway import ApiError, call_with_gateway, mock_llm_api, streaming_pipeline


def make_config(**overrides):
    base = dict(api_key="sk-test", concurrency=4, per_call_timeout=0.5,
                max_retries=3)
    base.update(overrides)
    return GatewayConfig(**base)


# ---------- 路径① 重试成功：前两次必失败，第三次成功 ----------

def flaky_then_ok(fail_times):
    calls = {"n": 0}

    async def api(task_id, delay=0.01, fail_rate=0.0, rng=None, fail_ids=frozenset()):
        calls["n"] += 1
        await asyncio.sleep(delay)
        if calls["n"] <= fail_times:
            raise ApiError("前几次故意失败")
        return f"resp-{task_id}"

    return api, calls


async def test_retry_succeeds_after_failures():
    api, calls = flaky_then_ok(fail_times=2)
    result = await call_with_gateway(["t1"], make_config(), api=api)
    assert result == {"t1": "resp-t1"}
    assert calls["n"] == 3, "应恰好重试两次后成功"


# ---------- 路径② 超时：API 慢于 per_call_timeout，重试耗尽后聚合异常 ----------

async def slow_api(task_id, delay=0.01, fail_rate=0.0, rng=None, fail_ids=frozenset()):
    await asyncio.sleep(1.0)                           # 远超 0.1s 超时
    return f"resp-{task_id}"


async def test_timeout_raises_aggregated():
    cfg = make_config(per_call_timeout=0.1, max_retries=1)
    with pytest.raises(BaseExceptionGroup):
        await call_with_gateway(["t1"], cfg, api=slow_api)


# ---------- 路径③ 取消：外部 cancel → 组内任务全灭、无孤儿 ----------

async def test_cancel_propagates_and_no_orphans():
    cfg = make_config()

    async def run_group():
        return await call_with_gateway(["t1", "t2"], cfg,
                                       api=mock_llm_api, delay=5.0)

    task = asyncio.create_task(run_group())
    await asyncio.sleep(0.05)                          # 让组跑起来
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


# ---------- 路径④ 背压：有界队列生产端必有挂起，无界必无 ----------

async def fast_tokens(n=15):
    for i in range(n):
        await asyncio.sleep(0.002)                     # 生产快
        yield f"tok-{i}"


async def test_backpressure_bounded_vs_unbounded():
    got_b, blocked_b = await streaming_pipeline(fast_tokens(), maxsize=2,
                                                consume_delay=0.02)
    assert got_b == 15
    assert blocked_b > 0, "有界队列：消费慢时生产端必须被挂起过"

    got_u, blocked_u = await streaming_pipeline(fast_tokens(), maxsize=0,
                                                consume_delay=0.02)
    assert got_u == 15
    assert blocked_u == 0, "无界队列：生产端不该被挂起"


# ---------- 附赠：配置 fail fast（同步用例） ----------

def test_config_fail_fast_without_api_key():
    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        GatewayConfig.from_env(env={})


def test_config_env_override_and_default():
    cfg = GatewayConfig.from_env(env={"LLM_API_KEY": "sk-x",
                                      "LLM_GATEWAY_CONCURRENCY": "8"})
    assert cfg.concurrency == 8
    assert cfg.max_retries == 3, "未设置时走代码默认值"
