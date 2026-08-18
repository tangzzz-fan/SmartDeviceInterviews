"""
T6-Q3 流式响应消费管道（挂项目 6.3）

异步生成器模拟逐 token 流式输出 → async for 消费；asyncio.Queue(maxsize)
做背压缓冲，时间戳级证据证明「缓冲满时生产端被挂起」；有界 vs 无界对照。

撞墙记录：
  墙1（人设翻车，如实留档）：写之前我拿 Combine 心智押注「队列满了
  生产端继续产，多的在队列里堆着（像 AnyPublisher 的 buffer 算子）」——
  实测 asyncio.Queue(maxsize=N) 满时 await put 把**生产端挂起**，背压
  信号沿 put 反传：生产端等待时长 = 消费端欠账（见输出里的挂起证据）。
  Combine 的 buffer 是「无限缓冲削峰」，asyncio 有界队列是「让生产者
  等消费者」——两种背压哲学，我押错了前者。教训：跨框架迁移先问
  「满了谁等」，别拿旧框架的默认行为猜新框架。
"""
import asyncio
import random
import time


# ---------- 异步生成器：模拟 LLM 逐 token 流式输出 ----------

async def token_stream(n_tokens=20, seed=7):
    """async def + yield = 异步生成器；yield 处挂起，控制权还给事件循环"""
    rng = random.Random(seed)
    for i in range(n_tokens):
        await asyncio.sleep(rng.uniform(0.01, 0.03))   # 生产快（平均 0.02s/token）
        yield f"tok-{i}"


# ---------- 直连版：async for 直接消费（无缓冲） ----------

async def direct_consume():
    t0 = time.perf_counter()
    got = []
    async for tok in token_stream(10):                 # 每次 anext 都是挂起点
        await asyncio.sleep(0.05)                      # 消费慢（0.05s/token）
        got.append(tok)
    return got, time.perf_counter() - t0


# ---------- 管道版：生产 → 有界 Queue → 消费（背压缓冲） ----------

async def pipeline(maxsize, n_tokens=20):
    q = asyncio.Queue(maxsize=maxsize)                 # maxsize=0 即无界
    blocked_total = 0.0
    blocked_events = []
    peak_qsize = 0

    async def producer():
        nonlocal blocked_total
        async for tok in token_stream(n_tokens):
            t_put = time.perf_counter()
            await q.put(tok)                           # 满时在这里挂起 = 背压
            waited = time.perf_counter() - t_put
            if waited > 0.005:                         # >5ms 视为被挂起过
                blocked_events.append((tok, waited))
                blocked_total += waited
            peak_qsize_update()

    def peak_qsize_update():
        nonlocal peak_qsize
        peak_qsize = max(peak_qsize, q.qsize())

    async def consumer():
        got = []
        while True:
            tok = await q.get()
            await asyncio.sleep(0.05)                  # 消费慢：0.05s/token
            got.append(tok)
            if tok == f"tok-{n_tokens - 1}":
                break
        return got

    t0 = time.perf_counter()
    prod = asyncio.create_task(producer())
    got = await consumer()
    await prod
    elapsed = time.perf_counter() - t0
    return {
        "maxsize": maxsize, "got": len(got), "elapsed": elapsed,
        "peak_qsize": peak_qsize, "blocked_events": blocked_events,
        "blocked_total": blocked_total,
    }


async def main():
    # ① 直连：async for 协议本身可用
    got, dt = await direct_consume()
    assert len(got) == 10
    print(f"直连消费：async for 拿到 {len(got)} token，耗时 {dt:.2f}s ✓")

    # ② 有界队列（maxsize=3）：背压证据
    r3 = await pipeline(maxsize=3)
    print(f"\n有界队列 maxsize=3：收齐 {r3['got']} token，耗时 {r3['elapsed']:.2f}s")
    print(f"  队列峰值长度 = {r3['peak_qsize']}（被压住了，没超过 3）")
    print(f"  生产端被挂起 {len(r3['blocked_events'])} 次，累计 {r3['blocked_total']:.2f}s")
    print("  挂起明细（前 3 条）:")
    for tok, w in r3["blocked_events"][:3]:
        print(f"    {tok}: put 被挂起 {w*1000:.0f} ms")
    assert r3["peak_qsize"] <= 3, "有界队列不该超过 maxsize"
    assert len(r3["blocked_events"]) > 0, "消费更慢时生产端必须有挂起证据"

    # ③ 无界队列（maxsize=0）：对照——生产端从不等待，队列无上限
    r0 = await pipeline(maxsize=0)
    print(f"\n无界队列 maxsize=0：收齐 {r0['got']} token，耗时 {r0['elapsed']:.2f}s")
    print(f"  队列峰值长度 = {r0['peak_qsize']}（生产端产完就堆着）")
    print(f"  生产端被挂起 {len(r0['blocked_events'])} 次（应为 0）")
    assert len(r0["blocked_events"]) == 0, "无界队列生产端不该被挂起"
    assert r0["peak_qsize"] > r3["peak_qsize"], "无界版峰值应显著更高"

    print("\n结论：有界版用「生产端等待」换内存上限（背压反传）；")
    print("无界版用「内存无上限」换生产端不等待——LLM 流式场景生产快消费慢时，")
    print("无界队列 = 把背压换成内存泄漏。背压方案选有界。")


if __name__ == "__main__":
    asyncio.run(main())
