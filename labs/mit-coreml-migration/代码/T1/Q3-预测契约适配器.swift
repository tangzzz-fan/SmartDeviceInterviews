// T1-Q3 预测契约：业务协议 vs CoreML 适配器骨架
import Foundation

struct Classification: Equatable {
    let label: String
    let confidence: Double
}

protocol ImageClassifier {
    func classify(imageID: String) throws -> Classification
}

/// 业务侧假实现：测试 / 预览用
struct FakeClassifier: ImageClassifier {
    func classify(imageID: String) throws -> Classification {
        Classification(label: "preview", confidence: 1.0)
    }
}

/// CoreML 适配器骨架：真实项目在此调用生成的模型类，不把生成类型泄漏到 UI
struct CoreMLClassifierAdapter: ImageClassifier {
    func classify(imageID: String) throws -> Classification {
        // 这里本应: let input = MyModelInput(image: ...); let out = try model.prediction(input: input)
        print("  [Adapter] 将 imageID=\(imageID) 转为模型输入特征（示意）")
        return Classification(label: "adapter-stub", confidence: 0.5)
    }
}

func run(_ classifier: ImageClassifier, id: String) {
    do {
        let result = try classifier.classify(imageID: id)
        print("业务层只看到 Classification: \(result)")
    } catch {
        print("业务层错误: \(error)")
    }
}

print("=== Fake ===")
run(FakeClassifier(), id: "img-1")
print("=== CoreML Adapter ===")
run(CoreMLClassifierAdapter(), id: "img-1")
print("结论: UI/Domain 依赖协议；生成的 *Input/*Output 停在 Adapter 内")
