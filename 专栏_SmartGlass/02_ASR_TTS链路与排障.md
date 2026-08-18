# 02 ASR / TTS 链路：流程、协议、排障、案例

真实水位：火山云 SDK 完成 ASR/TTS 接入，引擎内部问题没实际改过。明天比的是**流程理解、定界方法论、App 侧治理**，不是假装做过声学算法。

## 零、诚实口径（先背这段）

> 这个项目里 ASR/TTS 用火山云 SDK，引擎是黑盒，我没有改过云端实现。我的工作在 App 层：采集、编排、播放、埋点。异常先定界到端侧、网络或云端——端侧我修，云端我把证据链打包推厂商，同时保证降级路径。链路原理我可以讲清楚，因为这条链路我按阶段拆过，也按这个方法排过端侧问题。

为什么有效：承认边界 → 展示方法论 → 亮出真实工程交付（埋点/定界/降级）→ 主动证明原理掌握。比编造「我修过 SDK 的 bug」安全且更专业。

---

## 一、火山 SDK 实际接到哪一层（集成面，不是一个按钮）

```
App 集成面
├── 鉴权：appid / token，过期刷新
├── 建连：WebSocket 长连接，可复用
├── Session：每次对话的识别/合成上下文
├── 音频契约：采样率、位深、声道、编码
├── 回调：partial / final / 错误码 / 合成 chunk
└── 生命周期：start / send / stop / cancel
```

面试话术：**「我用的是火山移动端 SDK，它封装了 WebSocket 二进制协议；但我理解这套协议，因为排查问题时要看懂 SDK 日志、reqid 和帧格式。」**

### ASR 关键流程

```
mic / 眼镜 PCM → 按帧切包(100–200ms) → 可选 VAD → 有界发送队列 → wss 推云端
云端：鉴权 + session start(采样率/编码/热词) → 边收边解码
    → 回推 partial(可被覆盖) 和 final(定稿) → 静音超阈值判定说完
```

五个必须能辨析的概念：

1. **partial vs final**：partial 会回退修正（「今天天汽」→「今天天气」）。UI 覆盖渲染；**进 LLM 必须等 final**。拿 partial 喂模型是典型事故。
2. **VAD / 端点**：判断用户说完。太灵敏一停顿就截断，太钝用户干等——是产品旋钮，不是调通即可。
3. **流式的意义**：识别与说话并行，说完后很快出 final，而不是整段录完再上传。
4. **音频格式契约**：16k / 16bit / mono / pcm（或 SDK 指定编码）。端云不一致的表现是识别全错或空结果——排查第一查项。
5. **连接 ≠ session**：WebSocket 可保活复用（省 TLS 握手）；每次对话通常新开 session，热词/上下文不混。

### TTS 关键流程

```
LLM token 流 → 按标点切句(第一句优先，避免半句提交) → 逐句送 TTS
云端：文本 → 韵律 → 声学 → 声码器 → 音频 chunk 流式回推
App：解码 → jitter buffer → 播放时钟取数 → 下行眼镜
```

四个必须能辨析的概念：

1. **边合成边播**：不等全文。TTS 首帧延迟是体验指标。
2. **jitter buffer**：网络到达突发、播放匀速。太小 underrun 卡顿，太大加延迟。经验预缓冲 200–500ms，用 underrun 计数调。
3. **切句策略**：太短请求多首帧反复等；太长首句晚。LLM 停在句子中间要等后续 token，不能把半句送去合成。
4. **打断即清理**：停播 + 清空 buffer + 取消在途 TTS，否则旧语音在新对话里突然响起。

### App 侧会话状态机（你的主战场）

```
Idle ─start→ Listening ─vad/stop→ Recognizing ─final→ Thinking
  ─first sentence→ Speaking ─barge-in/done→ Interrupted → Listening
  任一状态 fail/timeout → Failed / Idle
```

实现要点：每个状态只允许一组合法事件，非法事件打日志丢弃；所有云回调带 `sessionId`，过期会话直接 return；Speaking 时是否继续采音决定打断体验和回声风险，必须显式取舍。

---

## 二、火山协议速查卡（被探「协议深度」时用；来源已核对，记不准的字段不硬背）

### 大模型流式 ASR

- 端点：`wss://openspeech.bytedance.com/api/v3/sauc/bigmodel`（`_nostream` 更准、`_async` 官方推荐）
- 鉴权头：`X-Api-Key` + `X-Api-Resource-Id`（如 `volc.seedasr.sauc.duration`）+ `X-Api-Request-Id`(uuid)
- 帧格式：4 字节头（版本/消息类型/序列化/压缩）+ payload_size + payload
- 消息类型：`0001` full-request、`0010` audio-only、`1001` server-response、`1111` error；**结束音频要发 final 包（结束标志）**，否则服务端按静音窗口自行断句，易丢尾字
- 音频：16k / 16bit / 单声道 PCM，每包 100–200ms（约 3200–6400 字节）
- 常用开关：`enable_itn`（数字日期规整）、`enable_punc`（标点）、`end_window_size`（默认 800ms 断句）、`corpus`（热词）
- 排查用响应头：`X-Api-Connect-Id`、`X-Tt-Logid`
- 常见错误码：`45000001` 参数无效、`45000081` 包等待超时、`45000151` 音频格式无效、`55000031` 服务繁忙

### TTS

- 双向流式 TTS 2.0：`wss://openspeech.bytedance.com/api/v3/tts/bidirection`
- 事件流：`StartConnection → StartSession(speaker/audio_params) → TaskRequest(text) → FinishSession`；**打断 = `CancelSession`**
- 音频格式：流式场景用 pcm / ogg_opus；wav 分块会重复文件头，不推荐
- 移动端 SDK：`com.bytedance.speechengine:speechengine_asr_tob` / `speechengine_tts_tob`，Maven：`artifact.bytedance.com/repository/Volcengine/`

> 使用纪律：这页用来证明「我研究过这条链路到协议层」。被追问具体字段名记不准时，说「以当时火山流式接口为准，细节我查文档」，**不现场编**。

---

## 三、排障方法论：三段定界（核心卖点，练成条件反射）

任何「识别不准 / 很慢 / 卡顿 / 自问自答」，第一步不是猜 SDK。

```
段1 端侧：采集、编码、状态机、播放、蓝牙/WiFi
段2 网络：DNS、TLS、WebSocket、弱网、代理
段3 云端：鉴权、配额、引擎实例、模型配置
```

### 定界四连

| 实验 | 若正常 | 若仍异常 |
|------|--------|----------|
| 换输入：本地标准 wav 直喂 ASR | 采集链路有问题 | 排除端侧 mic / 眼镜上行 |
| 换输出：TTS chunk 落盘用系统播放器播 | 播放管线 / 蓝牙音频有问题 | 排除 App 播放器 |
| 换网络：Wi-Fi / 蜂窝 / 办公网 | 网络段 | 排除单一网络环境 |
| 换客户端：官方 demo 或最小复现工程 | 你的集成参数 / 状态机 | demo 也挂 → 云端，带 requestId 提工单 |

### 五步口述

> 第一，复现并量化：必现还是偶发，频率多少，拿到一条完整路径。
> 第二，埋点分段：看 t0–t8 哪一段劣化。
> 第三，定界四连，把问题压到一段。
> 第四，固化证据：session 参数、requestId、时间戳、音频样本。
> 第五，分流：端侧自己修；云端推厂商，同时 App 加降级。

**加分句**：SDK 是黑盒，问题边界不是黑盒。我的职责是让厂商支持从「帮我查查」变成「确认这个 requestId」，并且服务抖动时用户还能看到文字。

### t0–t8 埋点（今晚背熟）

```
t0 用户触发        t1 首帧采音       t2 首个 chunk 上行
t3 云端收包(若暴露) t4 ASR 首个 partial t5 LLM 首 token
t6 TTS 首帧        t7 App 收到首段音频 t8 眼镜/手机开播
```

体感延迟 ≈ t8 - t0。优化看占比不看口号：LLM 首 token 往往是大头；弱网时 t2→t4 和 t6→t8 会爆。

### 日志字段最小集（被问「你怎么定位」直接报）

```
sessionId, deviceId, requestId
phase, t0..t8, durationMs
audioFormat, sampleRate, channels
wsReuse: bool
asrErrorCode, ttsErrorCode
bufferLevelMs, underrunCount
bleState, wifiState, rssi, networkType
```

没有这些字段线上只能猜；有了才能把「慢」变成「t2 到 t4 平均从 300ms 变成 1800ms」。

---

## 四、八个案例（C1/C5/C6/C7 必会，其余各能讲 90 秒）

呈现纪律：App 层可主导定位的按亲历讲；涉及云端机理的说「定界后确认在云端，我推动工单并做降级」。**不说「我修了火山引擎」。**

### C1 首包延迟突然变差
- 现象：用户说反应变慢，无发版。
- 排查：t0–t8 对比劣化集中在 t2→t4；抓包发现每次对话重新 TCP + TLS。
- 根因：会话管理改动导致 WebSocket 复用失效，每次冷建连，弱网下握手 300–500ms 被放大。
- 处理：连接保活 + 预建连；session 仍按次开启；`wsReuse` 打点防回归。
- 口述骨架：先分段。ASR 首包变慢我先看连接是否复用——TLS 握手是弱网下最容易被忽略的延迟小偷。

### C2 播放中识别出 TTS 自己的声音（自问自答）
- 现象：眼镜一边播报一边又开新一轮问答。
- 排查：对比「播放中采音」和「静音采音」的 ASR 文本，partial 与当前播报一致。
- 根因：扬声器到 mic 回声；AEC 参考信号缺失/未对齐，或播放态仍按正常阈值做 VAD。
- 处理：短期 Speaking 态暂停 ASR 或提高 VAD 阈值（打断变弱但止血）；产品要 barge-in 则固件 AEC 用下行 PCM 作参考，App 负责播放时间戳与采音对齐。
- 取舍必须说：停采稳但打断差；持续采音体验好但回声误触发。这是固件和 App 的协同题，不是单端能吹的。

### C3 partial 抖动、错误文本进 LLM
- 现象：字幕闪烁回退；偶发答非所问。
- 根因：把 partial 当追加渲染；或端点提前、final 没到就送下游。
- 处理：UI 覆盖式渲染；下游只消费 final；final 看门狗超时才允许用最后 partial 兜底并打点。
- 价值：partial/final 是流式 ASR 的照妖镜，被问「你真懂这条链路吗」时用。

### C4 TTS 卡顿 / 爆音
- 现象：弱网下播报一截一截，偶发爆音。
- 排查：underrun 计数上升；chunk 到达突发、播放匀速，buffer 被掏空。
- 根因：jitter buffer 阈值过小，或解码跟不上，或下行抖动。
- 处理：开播前预缓冲到阈值；underrun 时暂停回补再续；弱网请求更低码率；换输出实验区分「合成音频坏」还是「播放链路坏」。
- Android 追问补一句：还要看 AudioTrack buffer 和音频焦点——焦点被导航/来电抢走却没停取数，也会 underrun 或叠音。

### C5 云端偶发超时（诚实主场，必会）
- 现象：低概率无识别结果或合成失败，本地难复现。
- 排查：四连排除端侧和单一网络；官方 demo 同期也有失败。
- 处理：① 固化 requestId、时间戳、session 参数、音频样本；② 提工单说「这个 id 在 12:03:11 返回 5xx」，不说「你们服务不行」；③ App 降级：ASR 失败重试一次再降级文字提示，TTS 失败展示文本；④ 云端可用率看板，抖动可观测。
- 价值：黑盒问题的标准工程处置——这就是「没修引擎但能把线上问题闭环」。

### C6 弱网音频队列堆爆（纯端侧，必会）
- 现象：弱网下内存涨、卡死或 OOM 风险；恢复网络后突然灌一堆过期语音。
- 根因：采集还在产生、发送变慢、无界队列、无背压。
- 处理：有界队列、语音场景丢旧保新；网络恢复后重建 session 不灌过期 PCM；给用户弱网提示。
- 同构：BLE 写队列、EventChannel 高频 notify 都是生产消费失衡——可主动把音频和 BLE 流控放一起讲。

### C7 半开连接导致识别静默失败（长连接通用题）
- 现象：切网、锁屏一段时间后再说话没结果，界面一直「正在听」。
- 排查：抓包发现 TCP 还开着但收不到任何服务端包——半开连接；链路无心跳，客户端误判健康。
- 根因：无应用层心跳；移动网络 NAT 空闲超时静默杀连接。
- 处理：应用层心跳（10–15s ping，3 次无 pong 判断）；指数退避重连（1s/2s/4s…封顶 30s），重连后重发上下文不丢会话；网络变化监听主动重建；每次请求带 Request-Id 便于对账。
- 价值：所有长连接系统（WebSocket/推送/BLE）的通用问题，证明传输层意识。

### C8 专业名词 / 人名识别错
- 现象：产品名、人名全错，通用 ASR 对低频词没先验。
- 处理：热词表（corpus）增强；替换词表纠错；ASR 结果进 LLM 前做一轮领域纠错 prompt；关键命令词端侧关键词识别保底。
- 价值：识别率 ≠ 体验率，领域适配是工程活。

---

## 五、火山集成被追问时的短答

| 问 | 答 |
|----|----|
| token 突然全挂 | 先查鉴权过期。表现是「昨天还能用，今天全失败」 |
| 识别乱码 / 空 | 先查采样率声道编码是否和 session 参数一致 |
| 错误怎么分类 | 鉴权 401/403 刷新；参数类改契约；5xx/超时重试+降级+工单 |
| 为什么不自己做 ASR | 当时要快速验证交互闭环。产品化补的是连接复用、状态机、埋点、降级，不是先自研模型 |
| 如果火山服务挂了 | 多层降级：重试 → 备用端点/一句话识别 → LLM 兜底话术 → 端侧提示；协议层抽象，供应商可切换 |
| 为什么 WebSocket 不用 HTTP | 实时双向：几十个音频包持续上下行，HTTP 握手与串行等待不可接受 |
| API 叫什么 | 以当时火山流式语音 SDK 为准。记不准不编，我讲的是 session、音频契约和回调模型 |

---

## 六、Android 音频差异（岗位会问：同一条链路映射过去）

| 问题 | iOS | Android |
|------|-----|---------|
| 采集 | AVAudioEngine / AudioUnit | AudioRecord，source=`VOICE_COMMUNICATION` 才有系统 AEC 机会 |
| 播放 | AVAudioPlayer / AudioUnit | AudioTrack MODE_STREAM，buffer 大小影响卡顿 |
| 焦点 | AVAudioSession category / interruption | AudioFocusRequest；丢焦点必须停 TTS 和采音 |
| 通话抢占 | interruption notification | AUDIOFOCUS_LOSS / LOSS_TRANSIENT |
| 蓝牙音频 | 不把 HFP 和 BLE GATT 混为一谈 | 经典蓝牙 SCO 与 BLE 数据通道是两条路 |
| 后台 | 真实播放会话维持窗口 | 前台服务 + microphone/connectedDevice 类型，厂商 ROM 另杀 |

口播：

> 语音链路搬到 Android，状态机可以复用，系统约束要重做。最大差异是音频焦点和后台：iOS 用 session category；Android 必须显式要焦点，丢焦点就要切状态机，否则会出现「TTS 还在写 AudioTrack，但系统已经把输出切走」。

---

## 七、今晚验收

- [ ] 诚实口径脱稿（录音 3 遍）
- [ ] 能画 ASR / TTS / 会话状态机三张图
- [ ] 三段定界 + 四连 + 五步一口气说完
- [ ] t0–t8 不看稿；日志字段最小集报得出
- [ ] C1/C5/C6/C7 各 2 分钟脱稿；C2/C3/C4/C8 各 90 秒
- [ ] partial/final、jitter buffer、VAD、切句、连接复用、心跳 能辨析
