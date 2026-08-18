# T7-Q3 并发网关 + 熔断（Semaphore 限流 + 熔断三态 + 降级）（参考解法）
import asyncio, random, time

class CircuitBreaker:
    def __init__(self, fail_threshold=3, open_seconds=0.15):
        self.fail_threshold = fail_threshold
        self.open_seconds = open_seconds
        self.failures = 0
        self.state = "closed"      # closed / open / half-open
        self.opened_at = 0.0

    async def call(self, fn, fallback):
        now = time.monotonic()
        if self.state == "open":
            if now - self.opened_at > self.open_seconds:
                self.state = "half-open"
            else:
                return fallback()
        try:
            r = await fn()
            self.failures = 0
            self.state = "closed"
            return r
        except Exception:
            self.failures += 1
            if self.state == "half-open" or self.failures >= self.fail_threshold:
                self.state = "open"
                self.opened_at = time.monotonic()
            raise

async def flaky(i):
    await asyncio.sleep(0.01)
    if random.random() < 0.6:
        raise RuntimeError("upstream fail")
    return f"ok({i})"

async def ok(i):
    await asyncio.sleep(0.01)
    return f"ok({i})"

async def main():
    random.seed(1)
    cb = CircuitBreaker(fail_threshold=3, open_seconds=0.15)
    sem = asyncio.Semaphore(4)
    async def run(i, fn):
        async with sem:
            return await cb.call(lambda: fn(i), fallback=lambda: "降级: 缓存")
    results = await asyncio.gather(*[run(i, flaky) for i in range(12)], return_exceptions=True)
    print("12 个 flaky 请求:", [str(r)[:12] for r in results])
    print("熔断状态:", cb.state, "失败计数:", cb.failures)
    await asyncio.sleep(0.18)
    print("半开窗口后状态:", cb.state)
    r = await cb.call(lambda: ok(99), fallback=lambda: "降级")
    print("半开试探成功:", r, "| 恢复为:", cb.state)

asyncio.run(main())
