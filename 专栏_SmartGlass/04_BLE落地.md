# 04 BLE 落地展示：从配网 SDK 到智能眼镜

蓝牙是本场要主动打的牌。来源不是「我调过 CoreBluetooth」，而是阿兹尔配网通信 SDK 的状态机、可靠传输、联调定责，加上商汤眼镜的 BLE 控制面。把两段经历挂到同一套工程方法上。

---

## 一、90 秒：蓝牙我到底做过什么

> 在阿兹尔我做过 SmartHome 配网通信 SDK：用状态机把发现、连接、下发网络、云注册、绑定收成一条可恢复可取消的流程，BLE 和 SoftAP 用策略模式切开。协议层不假设系统可靠投递，应用层自己做窗口、序号和幂等。
>
> 在商汤眼镜项目，BLE 是控制面：配对、能力协商、心跳、打断、状态同步。大流量音频走 WiFi。所以我不是把 PCM 塞进 GATT，而是按带宽和时延把通道切开。
>
> 跨端上，内部插件 `smart_home_ble` 把扫描连接和配网进度封成 Dart API；Android 侧我按同一契约翻译，重点处理 GATT 串行、MTU、CCCD 和权限差异。

---

## 二、BLE 概念速查（脱口而出）

| 概念 | 一句话 |
|------|--------|
| GATT | 数据读写模型：Service → Characteristic → Descriptor 的树 |
| Notify / Indicate | 外设主动推数据；Indicate 有 ACK，Notify 没有 |
| Write / Without Response | 带应答可靠但慢；无应答快但丢，需应用层 ACK |
| MTU | 单次 ATT 可写长度，默认 23（payload 20），协商后最大 517；Android 必须 `requestMtu` |
| 连接参数 | connection interval / slave latency / supervision timeout，掉线与延迟的根源 |
| RSSI | 信号强度，弱信号预警用 |
| Bonding | 交换密钥加密连接 |

**MTU 为什么重要**：不协商，OTA 和音频信令都会慢且碎。
**BLE vs 经典蓝牙**：经典蓝牙面向持续流（A2DP 音频），功耗高；BLE 面向短包低频交互、可休眠，适合控制与事件。

---

## 三、眼镜场景里 BLE 负责什么

```
控制面 BLE                     数据面 WiFi
扫描 / 连接 / 重连              PCM 上行
能力查询                       Token / TTS 下行
心跳 / RSSI                    OTA
打断 / 停止（必须低时延）
配网凭证下发
会话状态查询（App 被杀后询问眼镜）
```

功耗：眼镜电池紧。BLE 常驻，WiFi 按需；WiFi 未 ready 禁止开对话，避免半连接刷失败。

被问「音频为什么不走 BLE」：16k 16bit mono 约 32kB/s，加上协议开销和重传，BLE 吞吐和抖动不适合主音频；控制指令可以。

---

## 四、连接状态机（两端都能讲）

```
Idle → Scanning(过滤 Service UUID / Manufacturer Data)
     → Connecting(超时进 Failed，不盲等)
     → Discovering(服务、特征、MTU、开 Notify)
     → Ready(允许业务)
     → Recovering(意外断连，指数退避 + 抖动)
     → Disconnected(用户主动或放弃)
```

规则：

- 未 Ready 不发业务指令；每个状态迁移都要有超时（连接 10s、发现 5s 量级）
- 重连成功必须重新发现服务和开 Notify，不复用旧 characteristic 引用
- 前台有限次退避（1s/2s/4s…封顶 30s），上限后给用户，不后台死循环扫
- RSSI 过差先预警，不要立刻暴力重连把射频打满

平台差异：

- Android：前台交互 `autoConnect=false`；后台指望系统捞回用 `true`（慢，且 ROM 不保证）；连接对象放 Service 不放 Activity
- iOS：`restoreIdentifier` + `willRestoreState` 有机会恢复已连接外设；恢复回调只做最小重建，不做云同步；**不是保证式唤醒**

---

## 五、可靠传输：系统 BLE 只是尽力投递

GATT notify / writeWithoutResponse 会丢。配网凭证和眼镜控制指令都需要应用层：

```
帧：seq | type | payload | crc
发送窗口：未确认帧不超过 N
ACK / NAK：超时重传
幂等：相同 commandId 只执行一次
```

- 眼镜控制指令尤其要幂等：重复「停止播报」必须安全
- 配网下发 WiFi 密码要加密，不能明文，也不能 Base64 当加密
- 成功标准不是「BLE 写成功」，而是设备真正联网或进入约定状态
- 大数据按 MTU 动态分包，失败退回 20 字节；Android 先 `requestMtu` 再切包
- 高频传感器 RingBuffer 丢旧保新；控制指令不能丢只能重传

这和 02 的音频有界队列是同一模型：**生产快于消费时必须有策略。音频可丢旧，控制指令不可丢。**

---

## 六、联调定责：体现工程能力的部分

面试官听过太多「蓝牙不稳定」。讲怎么证明是谁的问题。

现象分类：连不上 / 连上无数据 / 偶发断 / 命令无响应。自底向上：

1. App：蓝牙开关、权限、是否 connected、回调还在不在
2. 空口：iOS PacketLogger / Android HCI snoop，看 ACL 是否活着、ATT notify 有没有到
3. 设备日志：发送计数、错误码
4. 定责矩阵：

| 观察 | 责任 |
|------|------|
| App 无 disconnect，ACL 仍连，ATT 有 notify，UI 没动 | App：delegate 丢了或线程切错 |
| ACL 连着，设备计数在增，空口没有 notify | 固件没发出或空口丢 |
| Reason `0x08` supervision timeout | 射频 / 距离 / 干扰 |
| Reason `0x13` 对端断开 | 设备主动断 |
| Reason `0x16` 本机断开 | 系统策略 / App 主动 |

生产侧要能导出：RSSI、断连原因、阶段耗时、机型 × 固件 × 系统版本。没有这些只能实验室猜。

眼镜补充：控制面 BLE 正常不等于数据面 WiFi 正常，UI 要拆开显示，避免「已连接」但对话不可用。

---

## 七、配网 → 眼镜的同构表 + 稳定性清单

| 配网 SDK 能力 | 眼镜怎么用 |
|---------------|------------|
| 发现 → 连接 → 凭证下发 → 云注册 | 发现 → 连接 → 能力协商 → 拉起 WiFi 数据面 |
| 失败可恢复、可取消 | 对话中 WiFi 失败可回退，BLE 控制仍可停播 |
| 错误三层：用户可感知 / 可重试 / 需支持 | 鉴权、弱网、云 5xx 同样分层 |
| 策略模式切 BLE / SoftAP | 策略切 BLE-only 降级 / WiFi 数据面 |
| Mock 无硬件回归 | Mock 眼镜 + 假 ASR/TTS 跑状态机 |
| 结构化日志 | sessionId + bleState + wifiState + t0–t8 |

常见故障速查：

| 现象 | 根因方向 | 解法 |
|------|----------|------|
| 息屏/后台掉线 | 系统 BLE 后台受限、Doze | 前台服务持连接、重连状态机、连接参数合理 |
| 扫描找不到 | 过滤条件错、广播周期长、权限缺 | UUID 过滤、扫描窗口匹配广播周期、查权限 |
| 连接即断 / GATT 133 | 对端主动断、栈异常 | status 分类重试；重启扫描而非无限重连 |
| 写入失败 / 丢数据 | MTU 未协商、并发写 | 先 requestMtu；写队列串行 |
| Notify 没数据 | 没写 CCCD / 权限 / 旧 Gatt 对象 | 逐项排查 |

口播：眼镜不是新的蓝牙世界观。它是同一套连接状态机，换了一条「控制面/数据面」的通道仲裁。我在配网里做过仲裁和降级，眼镜把大流量从 BLE 挪到 WiFi，是同一判断。

---

## 八、现场白板：从扫描到 Ready

```
App                          眼镜
 |-- scan (UUID filter) -->  advertise
 |<-- discovered ------------|
 |-- connect --------------->|
 |<-- connected --------------|
 |-- request MTU ----------->|     // Android 显式
 |-- discover services ----->|
 |-- enable notify + CCCD -->|
 |-- handshake (seq/key) --->|
 |<-- capability (wifi?) ----|
 Ready: 控制面可用
 用户开对话
 |-- BLE: start wifi ------->|
 |-- WiFi TCP/WS ----------->|
 数据面可用；BLE 转心跳 + 打断
```

讲到这里停。**不主动展开 BLE Audio / LC3。**

---

## 九、短问答

- **如何提高连接成功率？** 过滤 UUID、控制扫描窗口、避免多连接打满、前台 `autoConnect=false`、按阶段打点、弱 RSSI 降频不空转。
- **App 进后台眼镜还能否打断？** 看系统是否允许蓝牙后台。iOS 有机会 restoration；Android 需前台服务。产品上接受「后台能力有上限」，会话状态存眼镜侧，App 回来先问设备。
- **Flutter 能直接做 BLE 吗？** 可以调插件，但状态机、分包、队列必须在原生。Flutter 消费状态；高频 notify 原生批处理。
- **配网是短连接、眼镜是长连接，差异怎么看？** 诚实承认差异 → 迁移三映射：状态机骨架同构、错误分层照搬、Mock 测试体系照搬；差异点（连接参数、功耗、持续吞吐）说出机制即可。
- **多台设备同时连（眼镜+耳机+手表）？** 共享射频预算、并发回调线程、音频路由冲突——答优先级仲裁与降级策略。

---

## 十、诚实边界（不越线）

- ❌ 不冒认 BLE Audio / LC3 / A2DP 编解码调优——口径：「音频通道由系统托管/走数据面，我负责的是 BLE 控制面与链路工程」
- ❌ 不冒认功耗专项调优——口径：「功耗我有度量方法论（Energy Log + 固定场景基线），眼镜的功耗预算分配是我接下来想深入的」
- ❌ 不说眼镜已有完整 Android CI，除非真有
- ✅ 主动打的：连接稳定性、可靠传输、联调定责、协议工程化、双端测试体系

---

## 十一、今晚验收

- [ ] 90 秒三段故事脱稿
- [ ] 白板建链序列 30 秒默画
- [ ] 控制面/数据面分工 + 定责矩阵能讲
- [ ] 能解释为什么音频不走 BLE、为什么打断走 BLE
- [ ] 诚实边界三条不越线
