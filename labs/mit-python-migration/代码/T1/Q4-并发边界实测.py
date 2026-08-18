# T1 Q4 并发边界实测（挂项目 1.5）
# 预测（作答稿已写，此处对照）：
#   CPU 密集：单线程 ≈ 多线程（甚至多线程更慢，GIL 轮流拿锁+切换开销），多进程 ≈ 快 N 倍
#   IO 密集：多线程 ≈ 快 N 倍（等待时释放 GIL），多进程也快但进程成本没必要
# 撞墙记录：
#   墙1：首版工作量 300 万次迭代，单次才 0.6s，多线程 vs 单线程差距被切换开销淹没，
#        看不出结论；扩到 500 万拉开基线。注意「多线程不快」本身就是 GIL 证据：
#        没有真并行才可能不快，真并行该快 4 倍。
#   墙2：写之前先立了个规矩——macOS 上 multiprocessing 默认 spawn，worker 必须
#        是模块级函数且在 __main__ 保护内跑（Swift 线养成的「先想环境约束」习惯），
#        这次没翻车；但 spawn 每次都要重启解释器，多进程 IO 场景的开销实测可见。
#   墙3：pool.map(fn, range(n)) 会把 range 里的元素当参数传给 fn，
#        cpu_work() 不收参直接 TypeError——改用 starmap(fn, [()]*n) 空参调用。
#        （想用 lambda 包一层也不行，lambda 不可 pickle。）

import time
import threading
import multiprocessing

N_WORKERS = 4


def cpu_work():
    """纯 Python CPU 密集：逐次累加，刻意不用 sum() 这类 C 实现。"""
    total = 0
    for i in range(5_000_000):
        total += i * i % 97
    return total


def io_work():
    """IO 密集：sleep 模拟网络等待。"""
    time.sleep(0.4)
    return "done"


def run_sequential(fn, n):
    start = time.perf_counter()
    for _ in range(n):
        fn()
    return time.perf_counter() - start


def run_threads(fn, n):
    start = time.perf_counter()
    ts = [threading.Thread(target=fn) for _ in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return time.perf_counter() - start


def run_processes(fn, n):
    start = time.perf_counter()
    with multiprocessing.Pool(n) as pool:
        pool.starmap(fn, [()] * n)   # 空参调用，避开 map 的强制传参
    return time.perf_counter() - start


def main():
    print("=== CPU 密集（4 个 cpu_work）===")
    t_seq = run_sequential(cpu_work, N_WORKERS)
    print(f"单线程:   {t_seq:.2f}s")
    t_thr = run_threads(cpu_work, N_WORKERS)
    print(f"多线程x4: {t_thr:.2f}s  <- GIL 下无并行，还多了切换开销")
    t_proc = run_processes(cpu_work, N_WORKERS)
    print(f"多进程x4: {t_proc:.2f}s  <- 各自独立解释器，真并行")

    print("\n=== IO 密集（8 个 0.4s sleep）===")
    t_seq = run_sequential(io_work, 8)
    print(f"单线程:   {t_seq:.2f}s")
    t_thr = run_threads(io_work, 8)
    print(f"多线程x8: {t_thr:.2f}s  <- 等待时释放 GIL，收益明显")
    t_proc = run_processes(io_work, 8)
    print(f"多进程x8: {t_proc:.2f}s  <- 也行，但进程创建成本没必要")

    print("\n结论：CPU 密集走多进程，IO 密集走多线程/asyncio——预测与实测一致")


if __name__ == "__main__":
    main()
