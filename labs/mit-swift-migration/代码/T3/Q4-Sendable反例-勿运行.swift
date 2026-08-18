// T3-Q4 反例文件（勿运行）：本文件故意编译不过，用于抄录 Swift 6 的真实 diagnostic。
// 验证方式：swiftc -swift-version 6 -typecheck Q4-Sendable反例-勿运行.swift
// 实测报错（2026-08-15，Swift 6.3.3）：
//   error: non-Sendable type 'Profile' of let 'shared' cannot exit main actor-isolated context
//   note:  class 'Profile' does not conform to the 'Sendable' protocol
// 病灶：顶层共享的可变 class 实例被送进 actor，且送出后原地还在改——
// 两个隔离域同时碰同一块可变状态，数据竞争的种子，编译器在类型层面直接拦。
import Foundation

final class Profile {
    var name: String = "Ada"
}

actor Mailbox {
    func store(_ p: Profile) { print(p.name) }
}

let box = Mailbox()
let shared = Profile() // 顶层共享的可变实例

func useAcross() async {
    await box.store(shared) // ← 报错行：非 Sendable 类型不能离开当前隔离域
    shared.name = "Bob"     // 送出去之后这边还在改——正是编译器担心的事
}

await useAcross()
