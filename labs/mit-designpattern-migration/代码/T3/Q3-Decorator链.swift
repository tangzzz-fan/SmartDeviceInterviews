// T3-Q3 Decorator 链：职责叠加 + 顺序敏感反例
import Foundation

protocol Requesting {
    func call(_ url: String) -> String
}

struct BaseRequest: Requesting {
    func call(_ url: String) -> String { "响应(\(url))" }
}

final class LoggingDecorator: Requesting {
    let wrapped: Requesting
    init(_ wrapped: Requesting) { self.wrapped = wrapped }

    func call(_ url: String) -> String {
        print("  [日志] 请求 \(url)")
        return wrapped.call(url)
    }
}

final class MetricsDecorator: Requesting {
    let wrapped: Requesting
    init(_ wrapped: Requesting) { self.wrapped = wrapped }

    func call(_ url: String) -> String {
        print("  [指标] +1")
        return wrapped.call(url)
    }
}

final class RetryDecorator: Requesting {
    let wrapped: Requesting
    let attempts: Int

    init(_ wrapped: Requesting, attempts: Int) {
        self.wrapped = wrapped
        self.attempts = attempts
    }

    func call(_ url: String) -> String {
        for i in 1...attempts {
            print("  [重试] 第\(i)次")
            if i == attempts {
                return wrapped.call(url)
            }
        }
        return "failed"
    }
}

print("链 A: 重试(外) > 日志 > 指标")
_ = RetryDecorator(
    LoggingDecorator(MetricsDecorator(BaseRequest())),
    attempts: 2
).call("/api")

print("\n链 B: 日志(外) > 重试 > 指标")
_ = LoggingDecorator(
    RetryDecorator(MetricsDecorator(BaseRequest()), attempts: 2)
).call("/api")

print("\n顺序敏感: 重试在外=每次尝试都记日志；重试在内=只记一次——Decorator 顺序改变行为")
