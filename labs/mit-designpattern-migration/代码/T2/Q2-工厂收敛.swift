// T2-Q2 工厂收敛：if/else 创建 → 静态工厂 + 协议
import Foundation

protocol Payment {
    func pay(_ amount: Double)
}

struct Alipay: Payment {
    func pay(_ amount: Double) { print("支付宝 ¥\(amount)") }
}

struct WeChatPay: Payment {
    func pay(_ amount: Double) { print("微信 ¥\(amount)") }
}

enum PaymentType {
    case alipay, wechat
}

enum PaymentFactory {
    static func make(_ type: PaymentType) -> Payment {
        switch type {
        case .alipay: return Alipay()
        case .wechat: return WeChatPay()
        }
    }
}

func checkout(_ type: PaymentType, _ amount: Double) {
    let payment: Payment = PaymentFactory.make(type)
    payment.pay(amount)
}

checkout(.alipay, 99)
checkout(.wechat, 199)
print("调用方只依赖协议；新增类型只改工厂一处")
