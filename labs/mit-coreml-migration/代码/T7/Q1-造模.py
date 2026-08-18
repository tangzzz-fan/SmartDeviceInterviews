# T7-Q1 torch 微型分类器 → CoreML（参考解法）
import pathlib
import torch
import torch.nn as nn
import coremltools as ct

ART = pathlib.Path(__file__).parent / ".artifacts"
ART.mkdir(exist_ok=True)


class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 3))

    def forward(self, x):
        return self.net(x)


torch.manual_seed(0)
model = MLP()
X = torch.randn(200, 4)
y = torch.randint(0, 3, (200,))
opt = torch.optim.Adam(model.parameters(), lr=0.02)
lossf = nn.CrossEntropyLoss()
for _ in range(200):
    opt.zero_grad()
    loss = lossf(model(X), y)
    loss.backward()
    opt.step()

traced = torch.jit.trace(model, torch.randn(1, 4))
mlmodel = ct.convert(
    traced,
    inputs=[ct.TensorType(name="input", shape=(1, 4))],
    outputs=[ct.TensorType(name="output")],
    convert_to="mlprogram",
)
mlmodel.save(str(ART / "model.mlpackage"))
spec = mlmodel.get_spec()
print("模型规格:")
for inp in spec.description.input:
    t = inp.type.WhichOneof("Type")
    print(f"  输入: {inp.name} type={t} shape={list(inp.type.multiArrayType.shape)}")
for out in spec.description.output:
    t = out.type.WhichOneof("Type")
    print(f"  输出: {out.name} type={t} shape={list(out.type.multiArrayType.shape)}")
print("已保存:", ART / "model.mlpackage")
print("说明: mlprogram 规范产物为 .mlpackage；classic 规范（.mlmodel）需 convert_to='neuralnetwork'")
