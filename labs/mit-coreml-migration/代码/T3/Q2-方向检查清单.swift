// T3-Q2 图像方向检查清单
import Foundation
import ImageIO

let cases: [(String, CGImagePropertyOrientation)] = [
    ("up", .up),
    ("right", .right),
    ("down", .down),
    ("left", .left),
]

print("CGImagePropertyOrientation 常用值:")
for (name, value) in cases {
    print("  \(name) raw=\(value.rawValue)")
}
print(
    """

    错方向后果: 训练时「头朝上」的特征，推理时横着喂 → Top1 可能系统性漂到别的类
    验证法: 同一张已知标签图，分别以 up/right 跑推理，对比 Top1 是否一致
    清单: ① 相机缓冲 orientation ② UIImage.imageOrientation ③ Vision handler 参数 ④ 训练导出是否已 baked
    """
)
