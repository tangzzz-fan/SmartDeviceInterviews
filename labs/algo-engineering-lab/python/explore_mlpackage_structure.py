"""
CoreML 入门辅助脚本：探索 .mlpackage 内部结构。

配合 docs/09-CoreML入门/02-Python到CoreML生成.md §6 使用。
运行方式：
    cd algo-engineering-lab
    uv sync --extra ml
    uv run python -m python.explore_mlpackage_structure
"""

from __future__ import annotations

import json
from pathlib import Path

import coremltools as ct


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def explore_package(pkg_path: Path) -> None:
    """打印 .mlpackage 目录结构、模型签名与权重信息。"""
    print(f"\n{'=' * 60}")
    print(f"探索模型包: {pkg_path.name}")
    print(f"{'=' * 60}")

    # ── 1. 目录结构 ──────────────────────────────────────
    print("\n📁 目录结构:")
    for p in sorted(pkg_path.rglob("*")):
        rel = p.relative_to(pkg_path)
        indent = "  " * len(rel.parts)
        if p.is_dir():
            print(f"{indent}📂 {p.name}/")
        else:
            size = p.stat().st_size
            unit = "B" if size < 1024 else f"{size / 1024:.1f} KB"
            print(f"{indent}📄 {p.name}  ({unit})")

    # ── 2. Manifest ──────────────────────────────────────
    manifest_path = pkg_path / "Manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        print("\n📋 Manifest.json (模型元数据):")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))

    # ── 3. 加载模型规格 ──────────────────────────────────
    model = ct.models.MLModel(str(pkg_path))
    spec = model.get_spec()

    print("\n🔧 模型类型:", spec.WhichOneof("Type"))

    # ── 4. 输入签名 ──────────────────────────────────────
    print("\n📥 输入签名:")
    for inp in spec.description.input:
        shape = list(inp.type.multiArrayType.shape)
        dtype = inp.type.multiArrayType.dataType
        # protobuf 枚举名
        dtype_name = {65568: "FLOAT32", 65552: "FLOAT16", 131104: "DOUBLE"}.get(
            dtype, str(dtype)
        )
        print(f"  名称: {inp.name}")
        print(f"  形状: {shape}")
        print(f"  类型: {dtype_name}")

    # ── 5. 输出签名 ──────────────────────────────────────
    print("\n📤 输出签名:")
    for out in spec.description.output:
        shape = list(out.type.multiArrayType.shape)
        print(f"  名称: {out.name}")
        print(f"  形状: {shape}")

    # ── 6. 权重统计（如果能读到） ────────────────────────
    try:
        import numpy as np

        # 通过 coremltools 读取权重
        print("\n⚖️  权重统计:")
        weight_dir = pkg_path / "Data" / "com.apple.CoreML" / "weights"
        if weight_dir.exists():
            for wf in sorted(weight_dir.iterdir()):
                data = np.fromfile(str(wf), dtype=np.uint8)
                print(f"  {wf.name}: {len(data)} bytes")
                # 尝试解读为 float32
                if len(data) % 4 == 0:
                    f32 = np.frombuffer(data, dtype=np.float32)
                    print(
                        f"    作为 FP32: {len(f32)} 个参数, "
                        f"range [{f32.min():.4f}, {f32.max():.4f}]"
                    )
                # 尝试解读为 float16
                if len(data) % 2 == 0:
                    f16 = np.frombuffer(data, dtype=np.float16)
                    print(
                        f"    作为 FP16: {len(f16)} 个参数, "
                        f"range [{f16.min():.4f}, {f16.max():.4f}]"
                    )
    except Exception as e:
        print(f"  (读取权重时跳过: {e})")

    # ── 7. 快速推理测试 ──────────────────────────────────
    print("\n🧪 快速推理测试:")
    import numpy as np

    in_name = spec.description.input[0].name
    in_shape = list(spec.description.input[0].type.multiArrayType.shape)
    test_input = np.zeros(in_shape, dtype=np.float32)
    out_key = spec.description.output[0].name
    result = model.predict({in_name: test_input})
    output = result[out_key]
    print(f"  输入: 全零向量 {in_shape}")
    print(f"  输出: {output}")
    print(f"  top-1 类别: {int(np.argmax(output))}")


def main() -> None:
    """探索本仓库所有 .mlpackage 模型。"""
    artifacts = _repo_root() / "artifacts" / "coreml"
    if not artifacts.exists():
        print("❌ artifacts/coreml/ 不存在。请先运行:")
        print("   uv run python -m python.generate_golden coreml_quant")
        return

    packages = sorted(artifacts.glob("*.mlpackage"))
    if not packages:
        print("❌ 未找到 .mlpackage 文件。请先运行:")
        print("   uv run python -m python.generate_golden coreml_quant")
        return

    print("🔍 CoreML 模型结构探索工具")
    print(f"找到 {len(packages)} 个模型包\n")

    for pkg in packages:
        explore_package(pkg)

    # ── 对比总结 ─────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("📊 模型对比总结")
    print(f"{'=' * 60}")
    for pkg in packages:
        total_size = sum(f.stat().st_size for f in pkg.rglob("*") if f.is_file())
        print(f"  {pkg.name}: {total_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
