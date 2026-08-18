// T8-Q2 VisionKit API 骨架（ImageAnalyzer + VKImageAnalysisRequest + Interaction）
// 说明: 需要 iOS 16+ / macOS 13+ 且 App 环境；CLI 只做编译骨架 + 请求类型清单
#if canImport(VisionKit)
import VisionKit
#endif

struct VisionKitSkeleton {
    static func describe() {
        #if canImport(VisionKit)
        let types = ["text (Live Text)", "visualLookup (视觉查找)", "subject (主体抠图)"]
        print("ImageAnalyzer 请求类型:")
        for t in types { print("  - \(t)") }
        print("集成姿势: ImageAnalyzer.analyze(_:configuration:) -> ImageAnalysis")
        print("           ImageAnalysisInteraction 附着到视图，提供复制/翻译/查询/扫码")
        print("待真机验证: 相机与实时交互需要 App + 真机；CLI 无法覆盖")
        #else
        print("当前平台无 VisionKit")
        #endif
    }
}

VisionKitSkeleton.describe()
