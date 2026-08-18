// T1-Q4 模式引入记账：朴素直写 vs Strategy 版
import Foundation

func fetchNaive(_ retries: Int) -> String {
    for i in 0...retries {
        if i == 1 { return "ok" }
    }
    return "failed"
}

protocol RetryStrategy {
    func shouldRetry(attempt: Int) -> Bool
}

struct FixedRetry: RetryStrategy {
    let max: Int
    func shouldRetry(attempt: Int) -> Bool { attempt < max }
}

func fetchStrategy(_ strategy: RetryStrategy) -> String {
    var attempt = 0
    while strategy.shouldRetry(attempt: attempt) {
        attempt += 1
        if attempt == 2 { return "ok" }
    }
    return "failed"
}

let naive = fetchNaive(2)
let strategic = fetchStrategy(FixedRetry(max: 2))
print("朴素版结果=\(naive)；Strategy 版结果=\(strategic)")
print("记账：问题=重试逻辑将来可能变；约束=当前仅固定重试、调用点 1 处；")
print("代价=Strategy 版多 1 协议 + 1 实现、+7 行；决策=暂不引入（策略唯一），注释写明提取条件；")
print("撤出条件=出现第二种策略（退避重试）时再提取协议")
