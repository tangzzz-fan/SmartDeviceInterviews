# T7-Q4 契约清单（参考解法）
import pathlib
import coremltools as ct

ART = pathlib.Path(__file__).parent / ".artifacts"
spec = ct.models.MLModel(str(ART / "model.mlpackage")).get_spec()

print("== 契约清单 ==")
for inp in spec.description.input:
    t = inp.type.WhichOneof("Type")
    print(f"输入: {inp.name} | type={t} | shape={list(inp.type.multiArrayType.shape)}")
for out in spec.description.output:
    t = out.type.WhichOneof("Type")
    print(f"输出: {out.name} | type={t} | shape={list(out.type.multiArrayType.shape)}")
print("预处理要求: 输入为 float32 张量 (1,4)，无归一化（训练即原始特征）；Swift 端按此契约构造")
print("标签表: 本示例为回归 logits（3 类 argmax），真实分类模型需同包标签表")
print("版本三元组: model=0.1.0 | preprocessing=0.1.0 | app_min=iOS 15（mlprogram 默认）")
