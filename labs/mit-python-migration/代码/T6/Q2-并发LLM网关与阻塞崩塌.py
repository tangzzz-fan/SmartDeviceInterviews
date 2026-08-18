"""
T6-Q2 并发 LLM API 网关（mock，挂项目 6.2）

四件套：Semaphore 限流 + 指数退避重试（带抖动）+ asyncio.timeout + TaskGroup 结构化取消。
阻塞崩塌实验：asyncio.sleep 版 vs time.sleep 版，并发度扫 {1, 4, 16}。

撞墙记录：
  墙1（预期翻车，人设留档）：阻塞崩塌实验写之前我拿 GCD 直觉押注：
  「time.sleep 版并发 16 应该接近 16 路并行，总耗时和并发 1 差不多」
  （GCD 里 dispatch_async 到并发队列就是多线程）。首跑实测：
  time.sleep 版并发 {1,4,16} 总耗时几乎完全一样（≈ 任务数×单次时长，
  串行爬完）——并发度加了耗时一分不降，崩塌曲线实锤（数字见输出表）。
  根因：事件循环只有一根线程，time.sleep 期间没有任何 await 点，
  调度器切不走——16 个协程排队轮流睡，等于串行。
  教训：asyncio 的并发上限 = await 点密度；阻塞调用把 await 点清零。
  墙2（真实翻车）：崩塌实验首跑直接炸——mock API 里 rng.random() 报
  AttributeError: 'NoneType' object has no attribute 'random'，根因是
  run_n 调 api 没传 rng（签名默认 None）且 fail_rate 默认 0.3 走了
  失败分支。修复：崩塌实验传 fail_rate=0.0 + 固定 rng。教训：mock 的
  可选参数默认值要安全（None 防御或默认 rng），别让测试路径撞生产默认值。
"""
import asyncio
import random
import time


class ApiError(Exception):
    pass


# ---------- mock API：异步版与阻塞版 ----------

async def mock_llm_api(task_id, delay=0.1, fail_rate=0.3, rng=None):
    """异步 mock：网络延迟用 asyncio.sleep（正确的异步姿势）"""
    await asyncio.sleep(delay)
    if rng.random() < fail_rate:
        raise ApiError(f"task-{task_id} 服务端 500")
    return f"resp-{task_id}"


async def mock_llm_api_blocking(task_id, delay=0.1, fail_rate=0.0, rng=None):
    """阻塞 mock：模拟同步 SDK（如老版 requests），time.sleep 霸占线程"""
    time.sleep(delay)                                  # 杀 loop 的元凶
    return f"resp-{task_id}"


# ---------- 网关：限流 + 重试 + 超时 + 结构化取消 ----------

async def call_with_gateway(n_tasks, concurrency, per_call_timeout=0.5,
                            max_retries=3, base_backoff=0.05,
                            fail_rate=0.3, seed=42, api=mock_llm_api):
    rng = random.Random(seed)                          # 可复现的失败注入
    sem = asyncio.Semaphore(concurrency)

    async def one_call(task_id):
        # 重试循环在闸门内：失败退避也占着并发名额（保守策略，防重试风暴）
        async with sem:                                # 入场闸门：限「同时在场数」
            for attempt in range(max_retries + 1):
                try:
                    async with asyncio.timeout(per_call_timeout):
                        return await api(task_id, fail_rate=fail_rate, rng=rng)
                except ApiError:
                    if attempt == max_retries:
                        raise
                    backoff = base_backoff * (2 ** attempt) * (0.5 + rng.random())
                    await asyncio.sleep(backoff)       # 指数退避 + 抖动

    async with asyncio.TaskGroup() as tg:              # 一个挂全组取消
        tasks = [tg.create_task(one_call(i)) for i in range(n_tasks)]
    results = [t.result() for t in tasks]
    return results


# ---------- 阻塞崩塌实验：并发度扫描（T5 纪律：耗时结论必须扫容量） ----------

async def run_n(api, n, concurrency, delay=0.1):
    sem = asyncio.Semaphore(concurrency)
    rng = random.Random(0)                             # 墙2 修复：rng 必须给，失败率设 0 保纯计时

    async def one(i):
        async with sem:
            return await api(i, delay=delay, fail_rate=0.0, rng=rng)

    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        ts = [tg.create_task(one(i)) for i in range(n)]
    await asyncio.gather(*ts)
    return time.perf_counter() - t0


async def collapse_experiment():
    n, delay = 16, 0.1
    print(f"\n阻塞崩塌实验（任务数={n}，单次时长={delay}s，理想全并行≈{delay}s）")
    print(f"{'并发度':>6} | {'asyncio.sleep 版':>16} | {'time.sleep 版':>14} | 加速了吗")
    print("-" * 62)
    for c in (1, 4, 16):
        t_async = await run_n(mock_llm_api, n, c, delay=delay)
        t_block = await run_n(mock_llm_api_blocking, n, c, delay=delay)
        scaled = "✓ 近线性加速" if t_async < delay * n / c * 1.6 else "✗"
        print(f"{c:>6} | {t_async:>13.3f}s | {t_block:>11.3f}s | 异步{scaled}；阻塞版{'串行爬完' if t_block > delay * n * 0.8 else '意外加速？'}")
    print("结论：asyncio.sleep 版并发度上去耗时下来（16 路并发 ≈ 0.1s 量级）；")
    print("time.sleep 版并发度加到 16 耗时一分不降——墙1 押注被实测打脸。")


# ---------- 主流程 ----------

async def main():
    # 网关功能验证：20 任务、并发 4、30% 失败率、可复现
    t0 = time.perf_counter()
    results = await call_with_gateway(20, concurrency=4, fail_rate=0.3, seed=42)
    print(f"网关：20 任务/并发4/失败率30% 全部成功（重试兜底），耗时 {time.perf_counter()-t0:.2f}s")
    assert len(results) == 20 and all(r.startswith("resp-") for r in results)
    print("  抽样:", results[:3])

    # 超时路径验证：delay 0.3 > timeout 0.2 → 重试耗尽后 CancelledError/TimeoutError 族
    try:
        async def slow_api(i, fail_rate=0.0, rng=None, **kw):
            await asyncio.sleep(0.3)
            return f"resp-{i}"
        await call_with_gateway(2, concurrency=2, per_call_timeout=0.2,
                                max_retries=1, base_backoff=0.01,
                                fail_rate=0.0, api=slow_api)
        print("超时实验：不该走到这")
    except* (asyncio.CancelledError, TimeoutError) as eg:
        print(f"超时路径：TaskGroup 聚合了 {len(eg.exceptions)} 个超时异常 ✓")

    # 取消传播验证：外部取消 → 组内任务全灭
    async def cancel_demo():
        async with asyncio.TaskGroup() as tg:
            for i in range(3):
                tg.create_task(mock_llm_api(i, delay=5.0))

    demo_task = asyncio.create_task(cancel_demo())
    await asyncio.sleep(0.05)
    demo_task.cancel()
    try:
        await demo_task
    except asyncio.CancelledError:
        print("取消路径：外部 cancel → TaskGroup 内全体任务被取消 ✓")

    await collapse_experiment()


if __name__ == "__main__":
    asyncio.run(main())
