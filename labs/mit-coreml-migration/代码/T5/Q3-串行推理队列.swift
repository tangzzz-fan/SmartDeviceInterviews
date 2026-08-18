// T5-Q3 串行推理队列
import Foundation

final class InferenceQueue {
    private let queue = DispatchQueue(label: "mit.coreml.infer")

    func submit(_ id: String, work: @escaping () -> Void) {
        queue.async {
            print("开始 \(id)")
            work()
            print("结束 \(id)")
        }
    }
}

let q = InferenceQueue()
let group = DispatchGroup()
for i in 1...3 {
    group.enter()
    q.submit("job-\(i)") {
        Thread.sleep(forTimeInterval: 0.05)
        group.leave()
    }
}
group.wait()
print("串行队列保证同一时刻只有一个推理，避免 GPU/ANE 争用打爆（示意）")
