// T4-Q2 Command 撤销栈 vs 闭包版
import Foundation

protocol Command {
    func execute()
    func undo()
}

final class Editor {
    var content = ""
    private var stack: [Command] = []

    func run(_ command: Command) {
        command.execute()
        stack.append(command)
        print("执行: \(content)")
    }

    func undo() {
        guard let command = stack.popLast() else { return }
        command.undo()
        print("撤销: \(content)")
    }
}

final class AppendCommand: Command {
    let text: String
    unowned var editor: Editor

    init(_ text: String, _ editor: Editor) {
        self.text = text
        self.editor = editor
    }

    func execute() { editor.content += text }
    func undo() { editor.content.removeLast(text.count) }
}

let editor = Editor()
editor.run(AppendCommand("你好", editor))
editor.run(AppendCommand("世界", editor))
editor.undo()
editor.undo()

print("\n闭包版只有 execute 没有 undo——要么成对存逆闭包（易错），要么没有通用撤销；")
print("命令对象有身份 + undo()，可入栈/重做/记录")
