// T8-Q3 三选一决策 CLI（系统能力 / 自建 Vision / 自定义 CoreML）
import Foundation

enum Decision { case systemVision, customVision, customCoreML }

func decide(scene: String, languageCoverageOK: Bool, structuredOutput: Bool, customCamera: Bool) -> Decision {
    if customCamera || !languageCoverageOK { return .customVision }
    if structuredOutput { return .customCoreML }
    return .systemVision
}

let cases = [
    ("扫码/证件识别", true, false, false),
    ("多语言 OCR + 定制体验取景框", false, false, true),
    ("结构化单据字段输出", true, true, false),
]
for (scene, lang, structured, camera) in cases {
    let d = decide(scene: scene, languageCoverageOK: lang, structuredOutput: structured, customCamera: camera)
    print("\(scene) -> \(d)")
    switch d {
    case .systemVision: print("   理由: 内建覆盖（Live Text/DataScanner），免费 on-device，先记账再升级")
    case .customVision: print("   理由: 语言覆盖不足或需要自定义相机体验 -> 自建 AVCaptureSession + Vision")
    case .customCoreML: print("   理由: 需要结构化输出/领域质量 -> 自定义模型（重走 T2 流水线 + T7 造模）")
    }
}
