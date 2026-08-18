// T2-Q4 命令式页面改写为 SwiftUI（挂载体 2.1 本体）
// 靶子见 Q4-UIKit原版参考.swift.txt：开关+计数+列表，命令式三处手动同步。
// 翻译原则：状态唯一化（UI = f(state)）、所有权按包装器声明、交互=改状态。
// 验收分段：模型层 + objectWillChange 证据走 CLI 硬验证；视图渲染待真机验证（C4 不冒充）。
import SwiftUI
import Combine

// ---- 模型层：引用型真理源（CLI 可实跑部分）----
final class SettingsModel: ObservableObject {
    @Published var darkMode = false                 // 开关状态：未来要接主题服务，属引用型真理源
    @Published var items: [String] = ["通知设置", "隐私", "关于"]
}

func verifyModelLogic() {
    print("=== Q4 模型层硬验证 ===")
    let model = SettingsModel()
    var bag = Set<AnyCancellable>()
    var emissions = 0
    model.objectWillChange
        .sink { _ in
            emissions += 1
            print("  objectWillChange 发射 #\(emissions)（变更前预告）")
        }
        .store(in: &bag)

    model.darkMode = true            // 原 darkSwitchChanged: + applyDarkMode 两步 → 现在一步：改状态
    model.items.append("账号与安全") // 原 reloadData → 现在改数据源本身，列表由框架自动刷
    assert(emissions == 2, "两次状态变更应预告两次")
    print("证据：改状态即广播，无需手写 target-action 回读与手动同步")
    print("模型终态：darkMode=\(model.darkMode), items=\(model.items)")
}
verifyModelLogic()

// ---- 视图层：声明式改写（渲染行为待真机验证）----
struct SettingsView: View {
    // 选型：本页自己创建并拥有，且是引用型 → @StateObject。
    // 理由（M3 三件套）：所有权=本页；生命周期=随本页身份存活、重算不重建（Q2 实验证过）。
    @StateObject private var model = SettingsModel()

    // 选型：页面私有的临时计数，不给任何下游共享 → @State。
    // 理由：值类型小状态；存储由框架按视图身份代管，body 重算不丢。
    @State private var visitCount = 0

    var body: some View {
        NavigationStack {
            Form {
                Section("外观") {
                    // 选型：$model.darkMode 取的是 Binding——借来的读写通道，不拥有。
                    // 对照 OC：不再 addTarget 回读 sender.isOn，Toggle 直接把写通道绑到真理源。
                    Toggle("深色模式", isOn: $model.darkMode)
                }
                Section("访问") {
                    // 对照 OC visitTapped：不再手动同步 countLabel.text，改状态、body 自己长出来
                    Button("访问次数 +1（当前 \(visitCount)）") {
                        visitCount += 1
                    }
                }
                Section("条目") {
                    // 选型：列表数据对子行是只读 → 普通值传递，不需要任何包装器
                    ForEach(model.items, id: \.self) { item in
                        ItemRow(title: item, isDark: model.darkMode)
                    }
                }
            }
            .navigationTitle("设置")
        }
    }
}

struct ItemRow: View {
    let title: String     // 只读传入：谁拥有？model。谁读？我。谁传？SettingsView。
    let isDark: Bool
    var body: some View {
        HStack {
            Text(title)
            Spacer()
            Text(isDark ? "深色" : "浅色")
                .foregroundStyle(.secondary)
        }
    }
}

print("Q4 视图层随本文件编译+运行通过（定义即类型检查）；渲染/交互/导航行为：待真机验证")
