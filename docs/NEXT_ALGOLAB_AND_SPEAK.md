# 下一轮：T15 关闭口述映射 + AlgoLab 专栏合并

## 目标

1. **T15**：把 SmartGlass「关闭口述」模式接到 Nirva 题库/白板（映射 + 练习页），不混 Glass JD 进题库 ID。
2. **AlgoLab**：从 `webapp` 开分支 `algo-lab`，把父目录 `/Developments/algo_lab` 的面试/文档精选合进本仓，作为独立专栏（+ 可选精简 lab 代码树）。

## 分支策略（已确认）

```
main
  └── webapp          # T01–T15 学习站
        └── algo-lab  # + 专栏_AlgoLab + labs/algo-engineering-lab（无 .build/.venv）
```

## T15 范围

| 交付 | 说明 |
| --- | --- |
| `speak_seed.py` | Glass prompt → Nirva `question_ids` / `whiteboard_ids` / 参考口径 |
| API | `GET/POST /api/practice/speak`：盲写 → 揭晓对照 |
| UI | `/practice/speak`；题详情/白板链到相关口述 |
| 口径 | Glass 音频双链路映射到加分项/WB7，并注明与 Nirva「BLE PCM」加分项差异 |

## AlgoLab 合并范围

**纳入**

| 来源 | 目标 |
| --- | --- |
| `algo_lab/iOS_Interview_Prep/*.md` | `专栏_AlgoLab/prep/` |
| `algo_lab/algo-engineering-lab/docs/**` | `专栏_AlgoLab/lab-docs/` |
| `algo_lab/Talk with K3/*.md`（无空文件） | `专栏_AlgoLab/talk-k3/` |
| 根 `README.md` / `JD.md` / 审计报告 | `专栏_AlgoLab/` 根 |
| lab：`Sources` `Tests` `python` `golden` `Package.swift` `README` `tickets` | `labs/algo-engineering-lab/` |

**排除**：`.build/`、`.venv/`、`artifacts/`、大图可保留 Talk 里 png（若体积可接受）

**不做**：不把 Algo 题混进 `A1` 题库 ID；不跑 Swift 测试进 CI（本轮只导入文档可浏览）。

## 验收

- [ ] `/practice/speak` 盲写后才显示参考；映射链到题/白板
- [ ] `python -m app.import_content` 导入 `专栏_AlgoLab`
- [ ] `/column/algolab` 可读 MD（含嵌套路径）
- [ ] `npm run build` 通过
