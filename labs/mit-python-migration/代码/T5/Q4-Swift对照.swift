// T5-Q4 Swift 对照：同一份求和/排序逻辑的编译语言基准（swiftc -O）
// 对照对象：Q4-Python耗时常数报告.py
// 数据规模对齐：求和 N=1_000_000（0..<N，与 Python 的 list(range(N)) 同内容），
// 排序 50_000 个随机数。
// 计时同纪律：重复多次取 min。
//
// 撞墙记录（真实翻车）：首版 reduce 计时用 `_ = data.reduce(...)`，
// 实测打出 0.0 ms、循环/reduce = inf×——swiftc -O 发现结果没人用，
// 整段归约直接被死码消除。修复：把结果存进全局 sReduce 并打印，
// 编译器才保留计算（副作用是黑盒，优化器不敢删）。
// 教训：跨语言基准先怀疑计时器，再怀疑编译器优化掉了你的被测代码。
import Foundation

let N = 1_000_000
let data = Array(0..<N)

func bench(_ repeats: Int, _ fn: () -> Void) -> Double {
    var best = Double.infinity
    for _ in 0..<repeats {
        let t0 = Date()
        fn()
        best = min(best, Date().timeIntervalSince(t0))
    }
    return best
}

// ① 循环求和（手写 for-in）
var sLoop: Int64 = 0
let tLoop = bench(7) {
    sLoop = 0
    for x in data { sLoop += Int64(x) }
}

// ② 高阶函数求和（reduce，对标 Python 内置 sum()）
var sReduce: Int64 = 0
let tReduce = bench(7) {
    sReduce = data.reduce(Int64(0)) { $0 + Int64($1) }   // 撞墙修复：结果必须有人用
}

// ③ 排序（sorted()，对标 Python sorted）
let sub = (0..<50_000).map { _ in Int.random(in: 0..<1_000_000) }
let tSort = bench(3) {
    _ = sub.sorted()
}

print("Swift 对照（swiftc -O）：")
print(String(format: "  循环求和     = %.1f ms", tLoop * 1000))
print(String(format: "  reduce 求和  = %.1f ms", tReduce * 1000))
print(String(format: "  sorted 排序  = %.1f ms（5 万元素）", tSort * 1000))
print(String(format: "  循环/reduce  = %.2f×（Python 同项是数十倍量级——编译后循环不再是瓶颈）",
             tLoop / tReduce))
print("  校验：sLoop =", sLoop, " sReduce =", sReduce)
