# T1 Q3 带参重试装饰器（挂项目 1.3）
# 撞墙记录：
#   墙1：第一版我只写了两层（retry 直接接 fn），结果 @retry(times=3) 报
#        TypeError——retry(times=3) 先执行返回的对象才是真装饰器，必须三层。
#   墙2：忘了 functools.wraps，打印 __name__ 出来是 'wrapper'，调试日志里
#        全是 wrapper 根本分不清谁是谁，加上 wraps 才好。
#   墙3：一开始用 bare except，把 KeyboardInterrupt 都吞了，改成只捕获指定异常。

import functools
import time


def retry(times, delay=0, exceptions=(Exception,)):
    """装饰器工厂：带参重试。times 为总尝试次数。"""
    def decorator(fn):
        @functools.wraps(fn)   # 不加这行，fn 的 __name__/__doc__ 会被 wrapper 顶掉
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    print(f"  [retry] {fn.__name__} 第{attempt}次失败: {e!r}")
                    if attempt == times:
                        raise            # 次数用完，原样抛出
                    if delay:
                        time.sleep(delay)
        return wrapper
    return decorator


_calls = {"n": 0}

@retry(times=3, delay=0.05, exceptions=(ConnectionError,))
def flaky_api():
    """前两次必失败、第三次成功的演示函数。"""
    _calls["n"] += 1
    if _calls["n"] < 3:
        raise ConnectionError(f"第{_calls['n']}次调用超时")
    return "200 OK"


print("调用结果:", flaky_api())
print("被装饰函数的 __name__:", flaky_api.__name__)   # 应为 flaky_api，证明 wraps 生效
print("被装饰函数的 __doc__:", flaky_api.__doc__)
assert flaky_api.__name__ == "flaky_api", "wraps 未生效"

# 超过重试次数应原样抛出
_calls2 = {"n": 0}

@retry(times=2, exceptions=(ValueError,))
def always_fail():
    _calls2["n"] += 1
    raise ValueError("永远失败")

try:
    always_fail()
except ValueError as e:
    print(f"超过次数后正确抛出: {e!r}（共尝试 {_calls2['n']} 次）")
    assert _calls2["n"] == 2
print("Q3 验证通过 ✔")
