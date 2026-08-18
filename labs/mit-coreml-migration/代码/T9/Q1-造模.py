# T9-Q1 Python 造 .mlpackage（参考解法，同 T7 Q1 的精简版）
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
print("造模完成:", ART / "model.mlpackage")

# 打印 Python 侧同一输入的输出（供 C++ 对拍）
import numpy as np
x = torch.tensor([[0.2, -0.3, 0.5, 0.8]], dtype=torch.float32)
with torch.no_grad():
    o = model(x).numpy()[0]
print("Python 输出:", np.round(o, 5), "argmax =", int(np.argmax(o)))
