# T8-Q2 文档切分器：固定+重叠 vs 按段落（参考解法）
doc = """SwiftUI 的状态管理把视图当作状态的函数。@State 用于视图私有状态。
@Observable 用于跨视图共享的模型对象。状态变化时依赖它的视图会自动重算。
组合优于继承：行为可以叠加，身份才需要继承。协议默认实现让组合也能复用。
"""

def chunk_fixed(text, size=12, overlap=3):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size - overlap)]

def chunk_paragraph(text):
    return [p.strip() for p in text.split("\n") if p.strip()]

fixed = chunk_fixed(doc)
para = chunk_paragraph(doc)
print("固定+重叠 chunks:")
for i, c in enumerate(fixed):
    print(f"  [{i}] {c[:30]}...")
print("\n按段落 chunks:")
for i, c in enumerate(para):
    print(f"  [{i}] {c[:30]}...")
print("\n边界效应: 固定切分把「@Observable 用于跨视图共享的模型对象。」拦腰截断——")
print("查询命中后半句时，主语在另一个 chunk，召回上下文缺主语，答案会编。")
