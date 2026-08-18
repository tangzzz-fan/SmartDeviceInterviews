// T4-Q3 Strategy 重构：if/else → 策略表
import Foundation

protocol DiscountStrategy {
    func discount(_ amount: Double) -> Double
}

struct NoDiscount: DiscountStrategy {
    func discount(_ amount: Double) -> Double { amount }
}

struct VipDiscount: DiscountStrategy {
    func discount(_ amount: Double) -> Double { amount * 0.8 }
}

struct PromoDiscount: DiscountStrategy {
    func discount(_ amount: Double) -> Double { amount * 0.5 }
}

enum DiscountRegistry {
    static let table: [String: DiscountStrategy] = [
        "normal": NoDiscount(),
        "vip": VipDiscount(),
        "promo": PromoDiscount(),
    ]
}

func priceNaive(_ channel: String, _ amount: Double) -> Double {
    if channel == "vip" { return amount * 0.8 }
    if channel == "promo" { return amount * 0.5 }
    return amount
}

func priceStrategy(_ channel: String, _ amount: Double) -> Double {
    (DiscountRegistry.table[channel] ?? NoDiscount()).discount(amount)
}

print("if/else: vip=\(priceNaive("vip", 100)) 新渠道=\(priceNaive("new", 100))")
print("策略表:  vip=\(priceStrategy("vip", 100)) 新渠道=\(priceStrategy("new", 100))")
print("新增策略只加注册表一行；策略固定场景 if/else 也够（记账后拒绝）")
