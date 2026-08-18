// T2-Q2 导出模型并打印体积
import Foundation
import CreateML
import CoreML

let rows: [[String: Double]] = (0..<120).map { i in
    let x = Double(i % 40) / 40.0
    let y = Double(i % 5) / 5.0
    return ["x": x, "y": y]
}
let labels = rows.map { ($0["x"]! + $0["y"]! > 0.8) ? "pos" : "neg" }
let data = try MLDataTable(dictionary: [
    "x": rows.map { $0["x"]! },
    "y": rows.map { $0["y"]! },
    "label": labels,
])

let classifier = try MLClassifier(trainingData: data, targetColumn: "label")
let outDir = FileManager.default.temporaryDirectory.appendingPathComponent("mit-coreml-t2", isDirectory: true)
try? FileManager.default.removeItem(at: outDir)
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let modelURL = outDir.appendingPathComponent("ToyClassifier.mlmodel")
try classifier.write(to: modelURL, metadata: nil)

let attrs = try FileManager.default.attributesOfItem(atPath: modelURL.path)
let size = attrs[.size] as? NSNumber ?? 0
print("导出: \(modelURL.path)")
print("体积: \(size.intValue) bytes")

// 顺便验证可被 CoreML 加载（编译可能发生在 load）
let compiled = try MLModel.compileModel(at: modelURL)
let compiledSize: Int = {
    var total = 0
    if let enumr = FileManager.default.enumerator(at: compiled, includingPropertiesForKeys: [.fileSizeKey]) {
        for case let file as URL in enumr {
            let s = (try? file.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
            total += s
        }
    }
    return total
}()
print("编译后目录: \(compiled.path)")
print("编译后合计约: \(compiledSize) bytes")
try? FileManager.default.removeItem(at: outDir)
try? FileManager.default.removeItem(at: compiled)
