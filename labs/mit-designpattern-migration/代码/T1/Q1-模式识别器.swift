// T1-Q1 模式识别器（参考解法）
import Foundation

struct Recognition {
    let name: String
    let pattern: String
    let problem: String
    let constraint: String
    let swiftEquiv: String
}

let items = [
    Recognition(
        name: "protocol delegate",
        pattern: "Strategy + Observer 混血",
        problem: "把决策/事件交给另一个对象处理",
        constraint: "一对一、weak 防环",
        swiftEquiv: "weak 协议或闭包属性"
    ),
    Recognition(
        name: "static let 单例",
        pattern: "Singleton",
        problem: "全局共享一份实例",
        constraint: "线程安全初始化",
        swiftEquiv: "static let shared（注意可变状态批评）"
    ),
    Recognition(
        name: "静态工厂",
        pattern: "Factory Method（静态形态）",
        problem: "按类型选择实现",
        constraint: "创建逻辑集中、调用方只认协议",
        swiftEquiv: "enum 静态工厂 + 协议"
    ),
    Recognition(
        name: "闭包回调",
        pattern: "Command 变体（行为参数化）",
        problem: "把一段行为当参数传",
        constraint: "轻量、无需撤销",
        swiftEquiv: "闭包直接承载"
    ),
]

for it in items {
    print(
        """
        === \(it.name) ===
        候选: \(it.pattern)
        问题: \(it.problem)
        约束: \(it.constraint)
        Swift 等价: \(it.swiftEquiv)
        """
    )
}
