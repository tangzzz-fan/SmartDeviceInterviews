// T1-Q4 端侧 vs 云记账 CLI
import Foundation

struct Ledger {
    let scene: String
    let latency: String
    let privacy: String
    let cost: String
    let updatable: String
    let coverage: String
    let decision: String
    let exitWhen: String
}

let sample = Ledger(
    scene: "离线识别植物（公园无网）",
    latency: "端侧 P95~50ms；云依赖网络 300ms–3s",
    privacy: "端侧图不上云；云需上传原图",
    cost: "端侧边际≈0；云按次计费",
    updatable: "端侧发版/差分更新；云可热更",
    coverage: "端侧受机型/系统限制；云统一",
    decision: "默认端侧；无模型命中时降级云（需用户同意）",
    exitWhen: "端侧 Top1<0.4 连续一周 或 模型体积>App 预算 15%"
)

print("场景: \(sample.scene)")
print("延迟: \(sample.latency)")
print("隐私: \(sample.privacy)")
print("成本: \(sample.cost)")
print("可更新: \(sample.updatable)")
print("覆盖率: \(sample.coverage)")
print("选型: \(sample.decision)")
print("撤出条件: \(sample.exitWhen)")
