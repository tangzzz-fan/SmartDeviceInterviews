// T6-Q4 收尾报告（收束重构的量化数据打印）
import Foundation

struct ReportRow {
    let item: String
    let worth: Bool
    let data: String
    let source: String
}

let rows = [
    ReportRow(
        item: "存储 Adapter（协议隔离）",
        worth: true,
        data: "改动点 12→1；换后端只需新实现 TaskStorage",
        source: "T3 结构型 M1（Adapter 翻译）+ T1 M5 记账"
    ),
    ReportRow(
        item: "Command 撤销栈",
        worth: true,
        data: "+18 行换 undo 能力；命令对象有身份",
        source: "T4 行为型 M3（Command 对象化）"
    ),
    ReportRow(
        item: "搜索 Strategy（多策略表）",
        worth: false,
        data: "只有一种策略，3 个类型换 0 收益——已按撤出条件移除",
        source: "T4 M1（闭包优先，策略唯一不引入）"
    ),
    ReportRow(
        item: "观察者总线（强凑）",
        worth: false,
        data: "账算不平：间接层 4 文件，事件仅 2 处——复攻中撤掉",
        source: "T1 M5（引入是负债决策）"
    ),
]

for row in rows {
    let tag = row.worth ? "值得" : "负债"
    print("[\(tag)] \(row.item) | \(row.data) | 依据: \(row.source)")
}

print("\n三个结论: ① 先对拍再重构（T6 M1） ② 记账防自我欺骗（T1 M5） ③ 拒绝也要有理由（T6 D3）")
print("撤出条件触发: 搜索 Strategy 因「策略唯一」撤除——模式可逆，撤出不是失败")
