// T4-Q4 Template Method 对拍：继承 vs 协议默认实现
import Foundation

protocol DataFlow {
    func fetchRaw() -> String
    func validate(_ raw: String) -> Bool
    func cache(_ data: String)
}

extension DataFlow {
    func run() -> String? {
        let raw = fetchRaw()
        guard validate(raw) else {
            print("校验失败")
            return nil
        }
        cache(raw)
        return raw
    }
}

class BaseFlow {
    func run() -> String? {
        let raw = fetchRaw()
        guard validate(raw) else {
            print("继承版校验失败")
            return nil
        }
        cache(raw)
        return raw
    }

    func fetchRaw() -> String { "" }
    func validate(_ raw: String) -> Bool { !raw.isEmpty }
    func cache(_ data: String) { print("继承版缓存") }
}

final class UserFlow: BaseFlow {
    override func fetchRaw() -> String { "user" }
}

struct OrderFlow: DataFlow {
    func fetchRaw() -> String { "order" }
    func validate(_ raw: String) -> Bool { raw.hasPrefix("order") }
    func cache(_ data: String) { print("协议版缓存 \(data)") }
}

print("继承版:", UserFlow().run() ?? "nil")
print("协议版:", OrderFlow().run() ?? "nil")
print("\n协议默认实现版：骨架只写一遍，新数据流=新结构体，可独立测试；修改点少于继承版")
