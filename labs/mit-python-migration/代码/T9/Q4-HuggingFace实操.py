# T9-Q4 HuggingFace 实操（参考解法：离线时如实标注「待验证」）
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

if HF_AVAILABLE:
    print("加载 tokenizer 与模型（如网络不可用且无本地缓存，会失败并如实记录）")
    name = "gpt2"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(name)
    text = "Swift 是最好的语言吗？"
    enc = tok(text, return_tensors="pt")
    print("编码:", enc["input_ids"].tolist())
    print("解码往返:", tok.decode(enc["input_ids"][0]))
    out = model.generate(**enc, max_new_tokens=5)
    print("生成:", tok.decode(out[0]))
    print("API 用法对照: from_pretrained(加载) -> tokenizer(text, return_tensors=pt)(编码) -> model.generate(推理) -> tokenizer.decode(解码)")
else:
    print("[离线/未装 transformers] 如实标注：本次未实跑，待真机验证。")
    print("标准工作流（文档模拟）:")
    print("  from transformers import AutoTokenizer, AutoModelForCausalLM")
    print("  tok = AutoTokenizer.from_pretrained('gpt2')")
    print("  model = AutoModelForCausalLM.from_pretrained('gpt2')")
    print("  enc = tok(text, return_tensors='pt'); model.generate(**enc, max_new_tokens=5); tok.decode(out[0])")
