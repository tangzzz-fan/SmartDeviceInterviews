// T1-Q3 类型安全的迷你解析层（学员第一版，挂载体 1.4 前置）
// 目标：泛型管道 + some/any 两版返回解析器 + 保留 PAT 撞墙注释
import Foundation

// 撞墙记录 1：第一版直接写 `any DecodablePayload<Output>` 报错
// "does not have primary associated types"——要在协议声明处用 <Output> 提升为主要关联类型
protocol DecodablePayload<Output> {
    associatedtype Output: Decodable
    var typeName: String { get }
}

struct UserPayload: DecodablePayload {
    struct Output: Decodable { let name: String }
    let typeName = "User"
}

struct ScorePayload: DecodablePayload {
    struct Output: Decodable { let score: Int }
    let typeName = "Score"
}

enum ParseError: Error { case badJSON, rejected(String) }

// 泛型管道：输入 Data → 解码 → 校验 → Result（where 子句把 Output 钉死成 Decodable）
func parse<P: DecodablePayload>(
    _ data: Data, with payload: P,
    validate: (P.Output) -> Bool
) -> Result<P.Output, ParseError> {
    do {
        let value = try JSONDecoder().decode(P.Output.self, from: data)
        return validate(value) ? .success(value) : .failure(.rejected(payload.typeName))
    } catch {
        return .failure(.badJSON)
    }
}

// some 版：返回类型固定一种（编译器知道底细，调用方只见协议）
func makeUserParser() -> some DecodablePayload { UserPayload() }

// any 版：装箱，运行时才见真身；Swift 5.7+ 用 primary associated types 钉住 Output
func makeAnyParser() -> any DecodablePayload<UserPayload.Output> { UserPayload() }

// ---- PAT 撞墙留档（以下写法在旧版 Swift 编译不过，故注释保留）----
// func makeOpaqueCollection() -> [DecodablePayload] { ... }
// 错误大意：Protocol 'DecodablePayload' can only be used as a generic constraint
// —— 关联类型没定死，元素格子尺寸与 eat/decode 签名都统一不了（见 C2 作答）

// ---- 运行验证 ----
let good = #"{"name":"Ada"}"#.data(using: .utf8)!
let r1 = parse(good, with: UserPayload(), validate: { !$0.name.isEmpty })
switch r1 {
case .success(let u): print("泛型管道成功:", u.name)
case .failure(let e): print("不应失败:", e)
}

let bad = #"{"score":"oops"}"#.data(using: .utf8)!
let r2 = parse(bad, with: ScorePayload(), validate: { $0.score >= 0 })
switch r2 {
case .success: print("不应成功")
case .failure(let e): print("泛型管道按预期拒绝:", e)
}

let someP = makeUserParser()
print("some 版类型账本：\(type(of: someP)) | typeName = \(someP.typeName)")
let anyP = makeAnyParser()
// 撞墙记录 2：type(of:) 对 any 值有重载歧义（报 cannot convert metatype），改用字符串插值
print("any 版装箱：\(type(of: anyP)) | typeName = \(anyP.typeName)")
// Result vs throws 取舍（口述佐证）：同步立即处理用 throws；要存进集合/延迟处理/异步回调用 Result
