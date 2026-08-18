// T1-Q2 三元组练习（参考解法：3 个问题 + 1 个「不用模式」结论）
import Foundation

struct Triple {
    let problem: String
    let constraint: String
    let solution: String
    let pattern: String
    let decision: String
}

let examples = [
    Triple(
        problem: "设置页多个 cell 点击行为不同",
        constraint: "行为数量固定",
        solution: "switch 分发",
        pattern: "Strategy（暂不需要）",
        decision: "不用模式：行为固定，if/else 可读性足够；>3 个策略再提取"
    ),
    Triple(
        problem: "登录状态变化通知多页面刷新",
        constraint: "一对多、生命周期各异",
        solution: "@Published + store(in:)",
        pattern: "Observer（Combine 承载）",
        decision: "引入：多播需求真实，内建承载"
    ),
    Triple(
        problem: "搜索输入防抖后请求",
        constraint: "请求昂贵、300ms 窗口",
        solution: "debounce 管道",
        pattern: "Observer/管道（Combine 内建）",
        decision: "引入：语言内建已覆盖，不写自定义模式"
    ),
]

for (i, e) in examples.enumerated() {
    print(
        """
        例 \(i + 1): 问题=\(e.problem) | 约束=\(e.constraint) | 解法=\(e.solution)
          候选=\(e.pattern) | 决策=\(e.decision)
        """
    )
}
