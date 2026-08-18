# 15 外部 Flutter 架构稿对照

来源：一外部分析稿，把项目写成「Flutter 智能眼镜 App + 日日新 HTTP + 火山 RTC 插件 + 蓝牙/Wi-Fi 双通道」。

**这份稿不能当自己的项目讲。** 它对的是分层和双通道思路；错的是把商汤眼镜配套说成 Flutter 主工程，并点名了一批你没用过的 pub.dev 插件和 RTC 封装。

放这里的目的：面试官若按这种图来问，你能当场切开「行业常见拆法」和「我实际交的货」。细节仍回 `01` `02` `03` `10` `12`。

---

## 一、应该放哪

| 稿里的块 | 仓库落点 | 怎么用 |
|----------|----------|--------|
| 一、分层架构 / 模块表 | `01` 白板、`08` 流程图、`12` 会话页 | 只借「UI / 业务 / 设备与语音在原生」这一刀 |
| 二、日日新 HTTP / Dio / 后端代理 | `02` 诚实口径 | 借「LLM 与 ASR/TTS 解耦」；不报稿里的 URL、模型名、Dio 代码 |
| 三、`volc_engine_rtc_web` | `02` | 明确：**不是**你的集成面。你接的是火山云移动端 ASR/TTS SDK |
| 四、BLE 控制 + Wi-Fi 数据 | `10` `04` | 口径一致，可当「行业标准做法」互证 |
| 五、分层排查 / 降级 | `02` `11` | 借分层隔离；埋点用 t0–t8，不要用 `print` logger 当答案 |
| 六、MFi / 上架 | 红线 | 不主动讲。没做过就不要认 |

不要把原文整篇拷进 `01` 或 `12` 当实现说明。

---

## 二、和真实项目差在哪（先背这张表）

| 稿里的说法 | 你的事实 | 明天怎么说 |
|------------|----------|------------|
| Flutter 智能眼镜 App | 商汤眼镜配套是 **iOS 从 0 到 1**；Flutter 在阿兹尔 SmartHome（Add-to-App、内部插件） | 「眼镜会话中枢是 iOS App。Flutter 是另一段混编和插件经历，不是把眼镜 App 用 Flutter 重写了一遍。」 |
| `flutter_blue_plus` / `moyoung_glasses_ble_plugin` | 眼镜 BLE 在原生；阿兹尔是内部插件 `smart_home_ble` | 不点名没交付过的开源插件。被问用哪个库：讲契约和 GATT 队列，不编 pub.dev |
| `volc_engine_rtc_web` + `config.json` 一站式 AIGC | 火山 **移动端 SDK**：采集、建连、session、partial/final、合成 chunk | 「我没有走 RTC 房间把 ASR/TTS/LLM 绑成一个 Agent。语音 SDK 和日日新是两路，App 做编排。」 |
| 客户端 Dio 直打 `token.sensenova.cn`，Key 写进 App | 对话接日日新；Key 与鉴权细节以当时接口为准，不现场编路径 | 稿里「后端代理保管 Key」是对的工程判断，可当建议，不说「我就是这样实现的」除非你做过 |
| BLoC / Riverpod 管设备+对话+UI | 眼镜侧状态机在原生；Flutter 只适合会话 UI | 回 `06` `12`：生命周期不属于 Widget 的状态不进 Dart |
| Wi-Fi 连眼镜热点再 WebSocket/RTSP | 数据面 WiFi 走 PCM / Token / TTS；iOS 不能任意切系统 Wi-Fi | 回 `10`：同局域网/热点方案有平台差异，不说成通用 Wi-Fi Direct |
| MFi、演示视频上架 | 没这条交付 | 不问不提 |

---

## 三、可以借鉴的四刀（和作战包对齐）

### 1. 分层：对，但主人不是 Flutter UI

稿的图把 Flutter UI 放最顶、原生放底，方向对。你的白板仍画 `01` 的三段：

```
眼镜（mic/扬声器、BLE、WiFi）
    BLE 控制面 / WiFi 数据面
手机 App（会话中枢、状态机、编排、埋点）  ← 商汤这段是 iOS
    火山 ASR/TTS          日日新 LLM
```

若岗位用 Flutter 做配套 App，会话页按 `12` 拆树：字幕单独听 partial，BLE/音频仍在原生插件，不进 `initState`。

### 2. 日日新与火山解耦：对，这就是方案 A

稿 3.3 方案 A：

> ASR（火山）→ 文本 → 日日新 → 回复文本 → TTS（火山）

这与 `00` `02` 口径一致，可以认。不要认稿里的 RTC 插件把三家绑进一个 `AigcConfig`。

被问「为什么不统一用火山方舟 LLM」：业务用日日新；语音链路用已接入的火山 SDK。App 的活是拼接、打断、降级，不是换模型品牌。

客户端把 API Key 写进 `lib/config.json`：**不要当自己的做法讲。** 可以说「Key 不应下发到端上，该走服务端代理」——这是常识，不是你的模块清单。

### 3. 双通道：对，直接回口径 A

控制面 BLE（配对、心跳、打断、状态），数据面 WiFi（PCM、TTS、OTA）。按需拉 WiFi，弱网降级仅控制。完整口播见 `10`。

稿里的 `GlassesSDK.connect`：先 BLE 再读热点再连 Wi-Fi，顺序对；具体类名、RTSP 不要背。iOS 侧 `NEHotspotConfiguration` 有权限和审核约束，`10` 已写，保持诚实。

### 4. 排查：方向对，深度用你的方法

| 稿 | 你要讲的 |
|----|----------|
| UI → 业务 → SDK → 硬件/云 | 三段定界：端侧 / 网络 / 云端（+ 固件） |
| `print` 时间戳 | t0–t8 + sessionId / reqid |
| BLE 重试 3 次、Wi-Fi 切 2.4G | 有界重试、状态机降级，不报没测过的次数 |
| ASR 失败改用文本、LLM 兜底话术 | 与 `02` 降级多层一致，可讲 |
| nRF Connect、Charles、adb | 可用；主案例仍是 `11` 的复用失效 |

---

## 四、面试官拿这张图来问时（30 秒）

> 分层和双通道我认同：UI 和会话状态要切开，控制走 BLE、大流量走 WiFi，ASR/TTS 和 LLM 也要切开。  
> 我交的货里，商汤眼镜配套的会话中枢是 iOS App，火山 SDK 管识别和合成，日日新管对话，App 做编排和降级。  
> Flutter 是阿兹尔那段：插件契约、Channel、把 iOS 实现翻译到 Android。如果这边配套 App 用 Flutter，我会把 BLE 和音频留在原生，Flutter 只做会话 UI，不会用 RTC 一站式插件把三家服务绑死，也不会让 PCM 过 Dart。

被追问稿里的插件名：  
> 这些是常见选型，不是我仓库里的依赖。我用的是内部 `smart_home_ble` 契约和原生火山 SDK。具体字段以当时文档为准。

---

## 五、红线（本篇专属）

1. 不说商汤眼镜 App 是 Flutter 项目。
2. 不说用过 `flutter_blue_plus`、`moyoung_glasses_ble_plugin`、`volc_engine_rtc_web`。
3. 不背 `https://token.sensenova.cn/v1`、`SenseNova-V6-Pro` 当自己的接口记忆；记不清就认。
4. 不说客户端保存日日新 API Key。
5. 不把 RTC Agent / roomId / ChatBot01 讲成自己的会话模型。
6. 不主动讲 MFi。
7. 双通道口径仍只讲 A，不把稿里的「音视频 RTSP」扩成新口径。
