// T3-Q1 网络层 Facade + Adapter
import Foundation

final class SDKClient {
    func request(path: String, completion: (String) -> Void) {
        completion("{\"ok\":true,\"data\":\"\(path)\"}")
    }
}

protocol HTTPClient {
    func get(_ path: String) -> String
}

final class SDKClientAdapter: HTTPClient {
    private let sdk = SDKClient()

    func get(_ path: String) -> String {
        var result = ""
        sdk.request(path: path) { result = $0 }
        return result
    }
}

final class APIClient {
    private let http: HTTPClient
    init(_ http: HTTPClient) { self.http = http }

    func fetchUser(id: String) -> String {
        http.get("/users/\(id)")
    }
}

let client = APIClient(SDKClientAdapter())
print("Facade 调用方只依赖 APIClient:", client.fetchUser(id: "42"))
print("Adapter 把 SDK 翻译成自己的 HTTPClient；换 SDK 只改 Adapter")
