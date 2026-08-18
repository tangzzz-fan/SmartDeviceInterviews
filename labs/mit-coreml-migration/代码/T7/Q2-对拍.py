# T7-Q2 转换前后对拍（参考解法）
import pathlib
import numpy as np
import torch
import coremltools as ct

ART = pathlib.Path(__file__).parent / ".artifacts"
coreml = ct.models.MLModel(str(ART / "model.mlpackage"))

x_np = np.array([[0.2, -0.3, 0.5, 0.8]], dtype=np.float32)
x_t = torch.from_numpy(x_np)

# torch 侧（重新构建同一结构并加载权重困难，这里用 coremltools 的预测 + torch 前向对比：
# 更简单做法：训练脚本里保存权重，此处用相同 seed 重建（参考解法演示对拍方法）
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

with torch.no_grad():
    torch_out = model(x_t).numpy()[0]

coreml_out = coreml.predict({"input": x_np})["output"][0]
err = float(np.max(np.abs(torch_out - coreml_out)))
top1_t = int(np.argmax(torch_out))
top1_c = int(np.argmax(coreml_out))
print("torch 输出:", np.round(torch_out, 5))
print("CoreML 输出:", np.round(coreml_out, 5))
print(f"最大绝对误差: {err:.2e}")
print(f"Top1 一致性: {top1_t == top1_c}（torch={top1_t}, coreml={top1_c}）")
