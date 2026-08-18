// T6-Q1 端到端：训练→导出→加载→预测
import Foundation
import CreateML
import CoreML

let xs = (0..<100).map { Double($0 % 20) / 20.0 }
let ys = (0..<100).map { Double($0 % 4) / 4.0 }
let labels = zip(xs, ys).map { $0 + $1 > 0.7 ? "pos" : "neg" }
let table = try MLDataTable(dictionary: ["x": xs, "y": ys, "label": labels])
let clf = try MLClassifier(trainingData: table, targetColumn: "label")

let dir = FileManager.default.temporaryDirectory.appendingPathComponent("mit-coreml-t6", isDirectory: true)
try? FileManager.default.removeItem(at: dir)
try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
let modelURL = dir.appendingPathComponent("E2E.mlmodel")
try clf.write(to: modelURL, metadata: nil)

let compiled = try MLModel.compileModel(at: modelURL)
let model = try MLModel(contentsOf: compiled)

let input = try MLDictionaryFeatureProvider(dictionary: [
    "x": MLFeatureValue(double: 0.9),
    "y": MLFeatureValue(double: 0.9),
])
let out = try model.prediction(from: input)
print("预测输出: \(out.featureNames.map { "\($0)=\(out.featureValue(for: $0)!)" }.joined(separator: ", "))")
print("端到端 OK")
try? FileManager.default.removeItem(at: dir)
try? FileManager.default.removeItem(at: compiled)
