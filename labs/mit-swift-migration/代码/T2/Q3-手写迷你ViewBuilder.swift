// T2-Q3 手写一个迷你 ViewBuilder（挂载体 2.3 前置 + C4 代码化）
// 目的：把 @ViewBuilder 的黑盒拆开——result builder 就是一组静态 build 方法，
// 编译器把我「顺序写下来的一段话」翻译成对它们的调用。
//
// 撞墙记录：第一版我写了 static func buildBlock<T>(_ components: T...) -> [T]，
// 想把所有语句塞进一个同类型数组——编译器当场拒绝：语句类型不一（String 和 Int）
// 根本统一不成一个 [T]。这才明白 ViewBuilder 里异构视图能共存，靠的不是装进数组，
// 而是 buildBlock 按「参数个数」重载、把各段原样包进元组/嵌套类型里（类型没被擦掉！）。

@resultBuilder
enum MiniBuilder {
    // 聚合：按参数个数重载，把各段语句原样打包（这里用元组演示形状）
    // 撞墙记录 3：实跑报 "missing argument for parameter #2 in call"——
    // 「Top」+ 一个 if 只有两段语句，我却只提供了 2 参/3 参重载，少了单参 buildBlock。
    // 教训：builder 要覆盖几种「语句个数」就得提供几个重载，一个都不能想当然。
    static func buildBlock<C0>(_ c0: C0) -> C0 {
        print("  [buildBlock] 单段：\(type(of: c0))")
        return c0
    }
    static func buildBlock<C0, C1>(_ c0: C0, _ c1: C1) -> (C0, C1) {
        print("  [buildBlock] 聚合 2 段：\(type(of: c0)) + \(type(of: c1))")
        return (c0, c1)
    }
    static func buildBlock<C0, C1, C2>(_ c0: C0, _ c1: C1, _ c2: C2) -> (C0, C1, C2) {
        print("  [buildBlock] 聚合 3 段：\(type(of: c0)) + \(type(of: c1)) + \(type(of: c2))")
        return (c0, c1, c2)
    }

    // if 无 else：分支是可选的
    static func buildOptional<C>(_ c: C?) -> C? {
        print("  [buildOptional] 包裹可选分支：\(String(describing: type(of: c)))")
        return c
    }

    // if/else：两分支类型可以不同，用同一个「二选一」容器接住
    // 撞墙记录 2：第一版只写了 first 没写 second，else 分支直接编译不过——
    // 两个方向的入口必须成对提供，编译器才知道把 else 往哪送。
    static func buildEither<First, Second>(first: First) -> MiniConditional<First, Second> {
        print("  [buildEither] 走 first 分支：\(type(of: first))")
        return .first(first)
    }
    static func buildEither<First, Second>(second: Second) -> MiniConditional<First, Second> {
        print("  [buildEither] 走 second 分支：\(type(of: second))")
        return .second(second)
    }
}

// 对应 SwiftUI 的 _ConditionalContent<First, Second>：位置恒定、类型二选一
enum MiniConditional<First, Second> {
    case first(First)
    case second(Second)
}

// 边界函数：builder 作用在闭包参数上，产出什么类型由 build 方法决定
func make<T>(@MiniBuilder content: () -> T) -> T {
    content()
}

// ---- 验证 1：多段语句合成一个整体，不用 return、不用数组 ----
print("=== 验证 1：if/else 两分支类型不同 ===")
let flag = true
let layout1 = make {
    "Header"                                  // String
    if flag { "亮灯文案" } else { 404 }       // String vs Int，故意不同型
    "Footer"                                  // String
}
print("layout1 的类型：\(type(of: layout1))")

// ---- 验证 2：if 无 else 走 buildOptional ----
print("=== 验证 2：if 无 else ===")
let showSecret = false
let layout2 = make {
    "Top"
    if showSecret { "Secret" }
}
print("layout2 的类型：\(type(of: layout2))")

// ---- 验证 3：翻转条件再跑一次，证明运行时只走一条分支但类型形状不变 ----
print("=== 验证 3：else 分支 ===")
let layout3 = make {
    "Header"
    if !flag { "亮灯文案" } else { 404 }
    "Footer"
}
assert(type(of: layout1) == type(of: layout3), "条件翻转不应改变整体类型——身份的位置恒定")
print("layout1 与 layout3 类型相同：\(type(of: layout1))")
print("结论：body 返回类型恒定靠 builder 保证；分支切换是『同位置换内容』，这正是 C4/C6 里 Identity 讨论的起点")
