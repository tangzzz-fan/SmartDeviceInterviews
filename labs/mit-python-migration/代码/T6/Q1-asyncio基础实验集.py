"""
T6-Q1 asyncio 基础实验集（挂项目 6.1）

四个实验：① 调用 async def 不执行；② 漏写 await 的静默翻车；
③ gather vs TaskGroup 错误处理差异；④ TaskGroup 取消传播与 finally 清理。

撞墙记录：
  墙1（真实翻车，实验设计）：实验③第一版让 bad_task 先炸（0.02s），
  首跑 gather 立即抛异常、两个兄弟任务没跑到「完成」——对比不出 gather
  「等兄弟跑完才抛」的本性（对照组选错，同 T3-Q3 教训复发：要选会犯病
  的版本）。修复：失败任务改成最后炸（bad_task_slow，0.2s），重跑后
  g1/g2 都打印「完成」gather 才抛，而 TaskGroup 侧 t1/t2 连「完成」都
  没打到就被取消——语义差异当场显形。
  墙2（人设翻车，如实留档）：实验②的漏 await 不是实验设计，是我第一版
  真写的——GCD 心智「调用即派发」，期待 data 是 'B-data'。首跑实测：
  data 是 <coroutine object fetch at 0x...>，函数体一行没跑，只有一行
  RuntimeWarning: coroutine 'fetch' was never awaited，退出码还是 0——
  静默缺失实锤。Swift 里漏 await 编译器直接拦，Python 这里没人拦。
  教训：协程是「待执行的说明书」，await/create_task 才是按下执行键。
"""
import asyncio


async def fetch(name, delay=0.1):
    print(f"  [fetch {name}] 开始")
    await asyncio.sleep(delay)
    print(f"  [fetch {name}] 结束")
    return f"{name}-data"


# ============ 实验① 调用 async def 到底发生了什么 ============
print("=" * 60)
print("实验①：直接调用 fetch('A')，不 await")
result = fetch("A")                       # GCD 心智：调用就派发了吧？
print("  返回值类型:", type(result))
print("  返回值:", result)
# 观察：函数体里的 print 没有输出——调用只是造了个对象

# ============ 实验② 漏写 await 的静默翻车 ============
print("=" * 60)
print("实验②：在协程里漏写 await，看它怎么静默缺失")

async def pipeline():
    data = fetch("B")                     # 第一版：漏了 await，以为是并发派发
    print("  拿到的 data:", data)         # 期待 'B-data'，实际？
    return data

asyncio.run(pipeline())

# ============ 实验③ gather vs TaskGroup 错误处理差异 ============
print("=" * 60)
print("实验③：一个任务抛异常时，gather 与 TaskGroup 的行为对照")

async def ok_task(name):
    await asyncio.sleep(0.1)
    print(f"  [{name}] 完成")
    return name

async def bad_task():
    await asyncio.sleep(0.02)
    raise ValueError("bad_task 炸了")

async def bad_task_slow():
    """墙1 修复版：失败者最后炸（0.2s），才能暴露 gather「等兄弟跑完」的本性"""
    await asyncio.sleep(0.2)
    raise ValueError("bad_task_slow 炸了")

async def demo_gather():
    try:
        await asyncio.gather(ok_task("g1"), bad_task_slow(), ok_task("g2"))
    except ValueError as e:
        print(f"  gather 抛出：{e}")

async def demo_taskgroup():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok_task("t1"))
            tg.create_task(bad_task())
            tg.create_task(ok_task("t2"))
    except* ValueError as eg:
        print(f"  TaskGroup 抛出 ExceptionGroup，含 {len(eg.exceptions)} 个异常：{eg.exceptions[0]}")

asyncio.run(demo_gather())
print("  ----")
asyncio.run(demo_taskgroup())

# ============ 实验④ TaskGroup 取消传播：finally 清理是否执行 ============
print("=" * 60)
print("实验④：组内一个任务炸了，兄弟任务被取消时 finally 跑不跑")

async def long_task(name):
    try:
        print(f"  [{name}] 开始长任务")
        await asyncio.sleep(5)
        print(f"  [{name}] 正常结束（不该看到这行）")
    finally:
        print(f"  [{name}] finally 清理执行 ✓")

async def demo_cancel():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(long_task("L1"))
            tg.create_task(long_task("L2"))
            tg.create_task(bad_task())
    except* ValueError:
        print("  组已收拾完毕，无孤儿任务")

asyncio.run(demo_cancel())
print("=" * 60)
print("全部实验结束")
