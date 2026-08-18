// T6-Q4 上线检查清单
import Foundation

struct Check {
    let name: String
    let ok: Bool
}

let checks = [
    Check(name: "契约文档齐全", ok: true),
    Check(name: "端侧回归集", ok: true),
    Check(name: "真机 ANE 度量", ok: false),
    Check(name: "回滚开关", ok: true),
    Check(name: "隐私文案/同意", ok: false),
    Check(name: "体积预算", ok: true),
]

var missing = 0
for c in checks {
    print("[\(c.ok ? "OK" : "缺")] \(c.name)")
    if !c.ok { missing += 1 }
}
print(missing == 0 ? "可上线" : "不可上线：缺 \(missing) 项（示例故意留缺项）")
