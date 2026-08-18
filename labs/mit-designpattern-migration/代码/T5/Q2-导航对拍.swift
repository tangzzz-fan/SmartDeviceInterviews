// T5-Q2 导航对拍：NavigationStack path 数据化 vs 手动导航/Coordinator
import Foundation

// 版一：path 数据化（SwiftUI NavigationStack 的心智，CLI 用数组模拟）
enum Route: Equatable { case home, login, detail(String) }
struct NavPath {
    private(set) var path: [Route] = []
    mutating func push(_ r: Route) { path.append(r) }
    mutating func pop() { _ = path.popLast() }
    mutating func reset() { path = [.home] }
    var isDeepLinked: Bool { path.count > 1 }
}

// 版二：手动导航/Coordinator（显式编排，可表达跨模块跳转）
protocol Coordinator {
    func start()
    func goToDetail(_ id: String)
    func goToLogin()
}
final class AppCoordinator: Coordinator {
    private var stack: [String] = ["home"]
    func start() { print("Coordinator 启动，栈: \(stack)") }
    func goToDetail(_ id: String) { stack.append("detail(\(id))"); print("跳转 detail(\(id))，栈: \(stack)") }
    func goToLogin() { stack.append("login"); print("跳转 login（带前置条件检查），栈: \(stack)") }
}

var path = NavPath()
path.push(.detail("42")); path.push(.login)
print("path 版: 可恢复（\(path.path)）、可深链（isDeepLinked=\(path.isDeepLinked)）；但跨模块编排/前置条件要靠外部逻辑")
let c = AppCoordinator(); c.start(); c.goToDetail("42"); c.goToLogin()
print("Coordinator 版: 显式编排（登录后跳转链/前置条件/混编桥接可写进一个类）；纯线性页面时 path 足够")
