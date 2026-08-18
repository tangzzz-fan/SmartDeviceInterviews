// T2-Q1 Create ML 表格分类器（合成数据）
import Foundation
import CreateML

let rows: [[String: String]] = (0..<200).map { i in
    let x = Double(i % 50) / 50.0
    let y = Double(i % 7) / 7.0
    let label = (x + y > 0.9) ? "pos" : "neg"
    return ["x": "\(x)", "y": "\(y)", "label": label]
}

let data = try MLDataTable(dictionary: [
    "x": rows.map { Double($0["x"]!)! },
    "y": rows.map { Double($0["y"]!)! },
    "label": rows.map { $0["label"]! },
])

let (train, test) = data.randomSplit(by: 0.8, seed: 42)
let classifier = try MLClassifier(trainingData: train, targetColumn: "label")
let trainMetrics = classifier.trainingMetrics
let testMetrics = classifier.evaluation(on: test)

print("训练 accuracy: \(trainMetrics.classificationError)") // classificationError = 1 - accuracy 近似口径，打印原始指标对象
print("训练指标: \(trainMetrics)")
print("测试指标: \(testMetrics)")
print("说明: Create ML 适合固定任务；指标必须在「目标设备分布」上再验一次")
