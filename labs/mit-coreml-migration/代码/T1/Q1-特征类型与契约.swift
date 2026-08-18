// T1-Q1 特征类型与契约
import Foundation
import CoreML

func describe(_ name: String, _ value: MLFeatureValue) {
    print("[\(name)] type=\(value.type) value=\(value)")
}

// MultiArray：常见于自定义网络的张量输入
let array = try! MLMultiArray(shape: [1, 3], dataType: .float32)
array[0] = NSNumber(value: 0.1)
array[1] = NSNumber(value: 0.5)
array[2] = NSNumber(value: 0.9)
describe("logits_in", MLFeatureValue(multiArray: array))

// 字符串：分类标签 / tokenizer 片段等
describe("label", MLFeatureValue(string: "cat"))

// 字典：稀疏特征或置信度图
describe("scores", try! MLFeatureValue(dictionary: ["cat": 0.8, "dog": 0.2] as [AnyHashable: NSNumber]))

print(
    """

    契约说明（调用方必须保证）:
      1. 特征名与模型输入名一致（不能想当然叫 image）
      2. 类型匹配（Image≠MultiArray）
      3. 形状匹配（[1,3] 不能塞 [3,1] 除非模型声明允许）
      4. 数值范围/预处理与训练一致（未标准化=静默准头崩）
    """
)
