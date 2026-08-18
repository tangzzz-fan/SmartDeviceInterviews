#!/bin/bash
# T9-Q2 编译 .mlpackage -> .mlmodelc
set -e
cd "$(dirname "$0")"
mkdir -p .artifacts/out
xcrun coremlcompiler compile .artifacts/model.mlpackage .artifacts/out
echo "编译产物:"
find .artifacts/out -maxdepth 2 | head -10
