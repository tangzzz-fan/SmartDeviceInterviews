// T5-Q3 DI 三态对拍：单例 vs 手动注入 vs @Environment（注释）
import Foundation
protocol Logging { func log(_ s: String) }
final class Logger: Logging { func log(_ s: String) { print("[log] \(s)") } }

// 版一：全局单例（依赖隐式、测试难换）
final class SingletonService {
    static let shared = SingletonService()
    let logger = Logger()
    func work() { logger.log("单例版") }
}

// 版二：手动注入（显式、可测试）
final class InjectedService {
    let logger: Logging
    init(logger: Logging) { self.logger = logger }
    func work() { logger.log("注入版") }
}

// 版三：@Environment（SwiftUI 官方通道，按视图树传递）
// struct EnvKey: EnvironmentKey { static let defaultValue = Logger() }
// extension EnvironmentValues { var logger: Logging { get { self[EnvKey.self] } set { self[EnvKey.self] = newValue } } }
// 使用时 @Environment(\.logger) var logger

SingletonService.shared.work()
InjectedService(logger: Logger()).work()
print("\n单例版: 依赖隐藏，测试要重置全局；手动注入版: 构造传参最显式，测试传假 Logger；")
print("@Environment 版: SwiftUI 树内按 key 注入，无需手动层层传参")
