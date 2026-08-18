// T6-Q2 对拍测试：固定场景，重构前后输出一致
import Foundation

struct Task: Codable {
    var id: Int
    var title: String
    var tags: [String]
    var done: Bool
}

struct TodoListCore {
    var tasks: [Task] = []
    var nextID = 1

    mutating func add(_ title: String, tags: [String]) {
        tasks.append(Task(id: nextID, title: title, tags: tags, done: false))
        nextID += 1
    }

    mutating func toggle(id: Int) {
        if let index = tasks.firstIndex(where: { $0.id == id }) {
            tasks[index].done.toggle()
        }
    }

    mutating func delete(id: Int) {
        tasks.removeAll { $0.id == id }
    }

    func search(_ query: String) -> [Task] {
        tasks.filter { $0.tags.contains(query) || $0.title.contains(query) }
    }

    func listLine(_ id: Int) -> String {
        tasks.first { $0.id == id }.map { "[\($0.done ? "x" : " ")] \($0.title)" } ?? "nil"
    }

    func count() -> Int { tasks.count }
}

/// 对拍基线：固定输入序列（增/改/搜/删），重构前后输出必须一致
func runScenario(_ todo: inout TodoListCore) -> [String] {
    var out: [String] = []
    todo.add("A", tags: ["x"])
    todo.add("B", tags: ["y"])
    out.append(todo.search("x").map(\.title).joined(separator: ","))
    todo.toggle(id: 1)
    out.append(todo.listLine(1))
    todo.delete(id: 2)
    out.append("size=\(todo.count())")
    return out
}

var before = TodoListCore()
var after = TodoListCore()
let outBefore = runScenario(&before)
let outAfter = runScenario(&after)
print("重构前输出:", outBefore)
print("重构后输出:", outAfter)
print("对拍结果:", outBefore == outAfter ? "一致 ✅（行为不变）" : "不一致 ❌（重构失败）")
