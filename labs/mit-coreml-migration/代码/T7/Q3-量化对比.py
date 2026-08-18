# T7-Q3 量化对比（参考解法：fp32 vs fp16）
import pathlib
import torch
import coremltools as ct

ART = pathlib.Path(__file__).parent / ".artifacts"


class MLP(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(torch.nn.Linear(4, 16), torch.nn.ReLU(), torch.nn.Linear(16, 3))

    def forward(self, x):
        return self.net(x)


torch.manual_seed(0)
model = MLP()
X = torch.randn(200, 4)
y = torch.randint(0, 3, (200,))
opt = torch.optim.Adam(model.parameters(), lr=0.02)
lossf = torch.nn.CrossEntropyLoss()
for _ in range(200):
    opt.zero_grad()
    loss = lossf(model(X), y)
    loss.backward()
    opt.step()
traced = torch.jit.trace(model, torch.randn(1, 4))

fp32 = ct.convert(traced, inputs=[ct.TensorType(name="input", shape=(1, 4))], outputs=[ct.TensorType(name="output")], convert_to="mlprogram")
fp16 = ct.convert(traced, inputs=[ct.TensorType(name="input", shape=(1, 4))], outputs=[ct.TensorType(name="output")], convert_to="mlprogram", compute_precision=ct.precision.FLOAT16)
fp32.save(str(ART / "model_fp32.mlpackage"))
fp16.save(str(ART / "model_fp16.mlpackage"))

s32 = (ART / "model_fp32.mlpackage").stat().st_size
s16 = (ART / "model_fp16.mlpackage").stat().st_size

import numpy as np
x = np.array([[0.2, -0.3, 0.5, 0.8]], dtype=np.float32)
o32 = ct.models.MLModel(str(ART / "model_fp32.mlpackage")).predict({"input": x})["output"][0]
o16 = ct.models.MLModel(str(ART / "model_fp16.mlpackage")).predict({"input": x})["output"][0]
top1_same = int(np.argmax(o32)) == int(np.argmax(o16))
print(f"fp32 体积: {s32} B")
print(f"fp16 体积: {s16} B（省 {100*(1-s16/s32):.1f}%）")
print(f"Top1 一致性: {top1_same}")
print("结论: fp16 默认可用（无损省体积）；int8/palettization 有损需端侧回归验收（三指标账本）。")
