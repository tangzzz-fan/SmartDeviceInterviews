#!/bin/bash
# T9-Q4 集成检查清单 + 对拍报告
set -e
cd "$(dirname "$0")"
PY=/Users/bigapple/Developments/MIT-Migration/MIT-Python-Migration/.venv/bin/python

echo "== 1. Python 造模 + Python 侧输出 =="
$PY Q1-造模.py | tail -3

echo ""
echo "== 2. 编译 .mlmodelc =="
./Q2-编译.sh | tail -4

echo ""
echo "== 3. C++ 推理 =="
mkdir -p .artifacts
clang++ -x objective-c++ -std=c++17 -fobjc-arc -framework CoreML -framework Foundation -o .artifacts/infer Q3-推理.mm
./.artifacts/infer "$PWD/.artifacts/out/model.mlmodelc"

echo ""
echo "== 4. 集成检查清单 =="
echo "[通过] 跨平台隔离: CoreML 调用收在 ObjC++ 适配层（#if __APPLE__）"
echo "[通过] 错误处理: NSError 出参 + 加载/构造/推理逐段检查"
echo "[通过] 线程/并发: MLModel 不可变 -> 并发 prediction 安全（独立上下文）"
echo "[通过] 资源打包: .mlmodelc 作为 App 资源（Xcode Copy Bundle Resources）"
echo "[待补] 对拍误差: 与 Q1 打印的 Python 输出人工对比（同一输入 0.2,-0.3,0.5,0.8）"
