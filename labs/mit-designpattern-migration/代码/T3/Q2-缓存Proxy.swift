// T3-Q2 缓存 Proxy：控访问 + 请求计数
import Foundation

protocol UserLoader {
    func fetch(id: String) -> String
}

final class RemoteUserLoader: UserLoader {
    var fetchCount = 0

    func fetch(id: String) -> String {
        fetchCount += 1
        return "用户[\(id)]"
    }
}

final class CacheUserLoaderProxy: UserLoader {
    private let wrapped: RemoteUserLoader
    private var cache: [String: String] = [:]

    init(_ wrapped: RemoteUserLoader) {
        self.wrapped = wrapped
    }

    func fetch(id: String) -> String {
        if let hit = cache[id] {
            print("命中: \(id)")
            return hit
        }
        let data = wrapped.fetch(id: id)
        cache[id] = data
        print("真实获取: \(id)")
        return data
    }
}

let remote = RemoteUserLoader()
let proxy = CacheUserLoaderProxy(remote)
_ = proxy.fetch(id: "1")
_ = proxy.fetch(id: "1")
_ = proxy.fetch(id: "2")
print("真实请求次数: \(remote.fetchCount)")
print("归属: Proxy（控制访问/缓存），不是 Decorator（未叠加职责）")
