// T4-Q1 Observer 三版对拍：通知心智 vs Combine vs 手写
import Foundation
import Combine

// 版一心智：NotificationCenter —— 注册后一直活到 removeObserver，忘移除=泄漏/崩溃风险
print("=== 版一 NotificationCenter 心智（注释说明，CLI 不真挂通知）===")
print("注册后一直活到 removeObserver；对象已释放却未移除 → 向野指针发消息")

// 版二：手写弱引用观察者表
protocol LoginObserver: AnyObject {
    func onLogin()
}

final class WeakBox {
    weak var value: LoginObserver?
    init(_ value: LoginObserver) { self.value = value }
}

final class HandRolledSubject {
    private var observers: [WeakBox] = []

    func add(_ observer: LoginObserver) {
        observers.append(WeakBox(observer))
    }

    func post() {
        observers.forEach { $0.value?.onLogin() }
    }
}

final class Page: LoginObserver {
    let name: String
    init(_ name: String) { self.name = name }
    func onLogin() { print("手写: \(name) 收到事件") }
}

print("\n=== 版二 手写弱引用表 ===")
let subject = HandRolledSubject()
let home = Page("首页")
let profile = Page("个人页")
subject.add(home)
subject.add(profile)
subject.post()

// 版三：Combine @Published
final class LoginStore: ObservableObject {
    @Published var isLoggedIn = false
    func login() { isLoggedIn = true }
}

print("\n=== 版三 Combine ===")
let store = LoginStore()
var cancellables = Set<AnyCancellable>()
store.$isLoggedIn
    .sink { print("Combine(持有): \($0)") }
    .store(in: &cancellables)

// 不 store：cancellable 立即释放 → 订阅取消；后续 login 收不到
var ephemeral: AnyCancellable? = store.$isLoggedIn
    .dropFirst() // 跳过订阅当下的初值，只看后续变化
    .sink { print("Combine(不存): 收到 \($0)（不该出现）") }
ephemeral = nil

store.login()

print(
    """

    对照:
      通知: 注册后一直活到 removeObserver，忘移除=崩溃/泄漏
      手写: 显式 add/remove，样板多，但可控弱引用
      Combine: 不 store = 释放即取消；上面 login 后只有「持有」打印 true
    """
)
