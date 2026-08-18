# T7-Q4 结构化输出管道：解析 + schema 校验 + 有限重试（参考解法）
import json, random

def mock_model_output():
    r = random.random()
    if r < 0.2:
        return "not json at all"
    if r < 0.4:
        return json.dumps({"title": "只有标题"})
    return json.dumps({"title": "任务", "due": "2026-08-18", "tags": ["llm"]})

SCHEMA = {"title": str, "due": str, "tags": list}

def validate(obj):
    if not isinstance(obj, dict):
        return False, "不是对象"
    for k, typ in SCHEMA.items():
        if k not in obj:
            return False, f"缺字段 {k}"
        if not isinstance(obj[k], typ):
            return False, f"{k} 类型错"
    return True, "ok"

def parse_with_retry(producer, *, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        raw = producer()
        try:
            obj = json.loads(raw)
        except Exception as e:
            print(f"第{attempt}次: 非法 JSON -> {type(e).__name__}")
            continue
        ok, msg = validate(obj)
        if ok:
            print(f"第{attempt}次: 校验通过 -> {obj}")
            return obj
        print(f"第{attempt}次: 校验失败({msg})")
    print(f"{max_attempts} 次后放弃，转降级")
    return None

random.seed(42)
result = parse_with_retry(mock_model_output, max_attempts=3)
print("最终结果:", result)
