// T2-Q1 视图是值现形记（学员第一版，挂载体 2.1 前置）
// 思路：在 CLI 无渲染环境里手动调 body，用 init 打点证明「视图值每次都是现造的」
// UIKit 旧心智里 init 一次用一辈子，这里要撞的就是这个直觉
import SwiftUI

struct RowView: View {
    let tag: Int
    init(_ tag: Int) {
        self.tag = tag
        print("  [init] RowView(\(tag)) 被造出来")
    }
    var body: some View {
        Text("行 \(tag)")
    }
}

struct ParentView: View {
    var body: some View {
        VStack {
            RowView(1)
            RowView(2)
        }
    }
}

// ---- 验证：手动调两次 body，看视图值是不是每次都重新造 ----
let parent = ParentView()
print("=== 第一次调 body ===")
_ = parent.body
print("=== 第二次调 body ===")
_ = parent.body

print("证据：两次 body 各自重新 init 了 RowView(1)/(2)——视图是值，body 是函数")
print("对照 UIKit：UIViewController init 一次实例活到 dismiss；这里连『实例』都没有，只有每次重算现造的描述")
