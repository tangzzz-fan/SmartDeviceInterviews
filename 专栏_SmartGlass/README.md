# 专栏 · SmartGlass（商汤智能眼镜面试材料）

从同级仓库 `SmartGlassInterview/综合版` **精选复制**而来，与本仓 Nirva「综合版」题库 **分栏并存、互不混 ID**。

## 定位差异（必读）

| | 本专栏 SmartGlass | 本仓综合版 Nirva |
| --- | --- | --- |
| 故事 | 商汤日日新智能眼镜 App | Founding iOS / 可穿戴通用题库 |
| 音频口径 | **锁定** BLE 控制面 + WiFi 数据面（PCM 不上 BLE） | 加分项仍可能讨论 BLE PCM 等选项 |
| 内容形态 | 项目复盘、链路 mermaid、自测 | 编号题库 A–AI、白板、STAR、模拟面 |

面试时：**一场只讲一种音频口径**。若投的是眼镜/双链路产品，优先用本专栏；若投 Nirva 类 founding iOS，以 `综合版/` 为准，本专栏作加分叙事参考。

## 本目录文件

- `00` 总览与诚实边界
- `01` 项目复盘 3 分钟
- `02` ASR/TTS 链路与排障
- `04` BLE 落地（对照用，勿与题库 B 题混记）
- `07` 今晚冲刺清单
- `08` 核心流程 mermaid
- `09` 自测题
- `10` 音频双链路选型（拍板口径）
- `11` 攻坚案例
- `13` 硬件渗透水位表
- `14` 反问
- `15` 外部稿对照 / 反冒认（Flutter 慎用）

未迁入：Flutter 深挖 `03/06/12`、视频 `16`（除非 JD 明确需要）。

## 同步

```bash
cd backend && source .venv/bin/activate
python -m app.import_content --path ../专栏_SmartGlass --force
```

网站导航：**专栏** → 浏览与 Mermaid 渲染。
