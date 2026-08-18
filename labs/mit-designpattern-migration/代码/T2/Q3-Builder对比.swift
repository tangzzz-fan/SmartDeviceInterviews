// T2-Q3 Builder vs 命名参数
import Foundation

struct Config {
    let apiKey: String
    let baseURL: String
    var timeout = 30.0
    var retries = 3
    var logEnabled = false
}

final class ConfigBuilder {
    private var apiKey: String?
    private var baseURL: String?
    private var timeout = 30.0
    private var retries = 3
    private var logEnabled = false

    func apiKey(_ value: String) -> Self {
        apiKey = value
        return self
    }

    func baseURL(_ value: String) -> Self {
        baseURL = value
        return self
    }

    func timeout(_ value: Double) -> Self {
        timeout = value
        return self
    }

    func build() -> Config? {
        guard let apiKey, let baseURL else { return nil }
        return Config(
            apiKey: apiKey,
            baseURL: baseURL,
            timeout: timeout,
            retries: retries,
            logEnabled: logEnabled
        )
    }
}

let namedParams = Config(apiKey: "k", baseURL: "u")
let built = ConfigBuilder().apiKey("k").baseURL("u").timeout(10).build()
print("命名参数版: 必选编译期强制，零样板（timeout=\(namedParams.timeout)）")
print("Builder 版: 多 1 类型、必选运行时校验（timeout=\(built?.timeout ?? -1)）")
print("结论: 本场景命名参数胜；Builder 只在交叉校验 + 不可变产物场景胜出")
