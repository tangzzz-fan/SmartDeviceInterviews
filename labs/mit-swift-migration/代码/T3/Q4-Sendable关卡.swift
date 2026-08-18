// T3-Q4 Sendable 关卡（挂载体 3.3 Sendable）
// 三幕：①全 let 的 struct 跨域畅通 ②可变 class 被编译器拦（反例文件实锤）
//       ③修复：值化。编译器拦的不变量：同一时刻只有一个隔离域能碰可变状态。
import Foundation

// ① 不可变值：全 let + 成员皆 Sendable → 天然可跨域
struct Snapshot: Sendable {
    let id: Int
    let name: String
}

// ③ 修复路径：把「该是值的东西」值化——OC 时代的 Profile class 改造成 Snapshot
actor Archive {
    private var stored: [Int: Snapshot] = [:]
    func deposit(_ s: Snapshot) {
        stored[s.id] = s
        print("  [Archive] 收入 Snapshot(id=\(s.id), name=\(s.name))")
    }
    func summary() -> String { "Archive 共 \(stored.count) 条" }
}

let archive = Archive()

// 跨域往返：顶层上下文 → Archive actor → 结果返回
let snap = Snapshot(id: 1, name: "Ada")
await archive.deposit(snap)
print("  存入成功：", await archive.summary())

// ② 反例实录（见 Q4-Sendable反例-勿运行.swift，swiftc -swift-version 6 实锤）：
//   error: non-Sendable type 'Profile' of let 'shared' cannot exit main actor-isolated context
//   note:  class 'Profile' does not conform to the 'Sendable' protocol
// 编译器拦的就是「可变引用跨域 = 两边同时读写 = 数据竞争的种子」。
//
// closure 为什么默认也不放心：它捕获了什么、捕获物是不是可变共享，编译器无法静态验证。
//
// @unchecked Sendable 的性质：人肉担保 + 关掉检查。只有真能证明
// 「跨域后不存在并发可变访问」（如内部全 let、或有锁且锁协议自洽）才敢标；
// 默默贴标签 = 把编译期保险丝拆了赌运气，出了事 TSan 见。
print("Q4 验证通过：不可变值畅通；可变引用被拦；值化是首选修法")
