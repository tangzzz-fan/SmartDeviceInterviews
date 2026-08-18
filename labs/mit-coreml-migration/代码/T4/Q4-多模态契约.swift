// T4-Q4 多模态契约字段
import Foundation

struct MultiModalContract {
    let imageFeature: String
    let textFeature: String
    let imageSize: String
    let textMaxTokens: Int
    let fusion: String
    let missingModality: String
}

let contract = MultiModalContract(
    imageFeature: "image: CVPixelBuffer 224x224 sRGB",
    textFeature: "tokens: MultiArray [1,32] int32",
    imageSize: "224x224 letterbox",
    textMaxTokens: 32,
    fusion: "late fusion / concat embedding（示意）",
    missingModality: "缺文本→纯视觉分支；缺图→拒识或降级云"
)

print("图: \(contract.imageFeature)")
print("文: \(contract.textFeature)")
print("图像几何: \(contract.imageSize)")
print("文本上限: \(contract.textMaxTokens)")
print("融合: \(contract.fusion)")
print("缺失策略: \(contract.missingModality)")
