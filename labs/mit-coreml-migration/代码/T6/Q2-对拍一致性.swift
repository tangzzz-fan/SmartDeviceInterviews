// T6-Q2 对拍：同一输入两次预测一致
import Foundation
import CreateML
import CoreML

let xs = (0..<80).map { Double($0 % 16) / 16.0 }
let ys = (0..<80).map { Double($0 % 3) / 3.0 }
let labels = zip(xs, ys).map { $0 + $1 > 0.6 ? "pos" : "neg" }
let table = try MLDataTable(dictionary: ["x": xs, "y": ys, "label": labels])
let clf = try MLClassifier(trainingData: table, targetColumn: "label")
let url = FileManager.default.temporaryDirectory.appendingPathComponent("pair.mlmodel")
try clf.write(to: url, metadata: nil)
let model = try MLModel(contentsOf: try MLModel.compileModel(at: url))

func predict(_ model: MLModel) throws -> String {
    let input = try MLDictionaryFeatureProvider(dictionary: [
        "x": MLFeatureValue(double: 0.8),
        "y": MLFeatureValue(double: 0.5),
    ])
    let out = try model.prediction(from: input)
    // 表格分类器通常输出 classLabel
    if let v = out.featureValue(for: "label") ?? out.featureValue(for: "classLabel") {
        return v.stringValue
    }
    return out.featureNames.sorted().map { "\($0)=\(out.featureValue(for: $0)!)" }.joined(separator: ";")
}

let a = try predict(model)
let b = try predict(model)
print("第一次: \(a)")
print("第二次: \(b)")
print(a == b ? "对拍一致 ✅" : "对拍不一致 ❌")
try? FileManager.default.removeItem(at: url)
