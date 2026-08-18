// T1-Q3 Prototype 对拍：值语义 vs class 深拷贝
import Foundation

final class Storage {
    var items: [String] = []
}

struct Draft {
    var storage: Storage
}

var a = Draft(storage: Storage())
a.storage.items.append("A1")
var b = a
b.storage.items.append("B1")
print(
    "struct 包 class: a=\(a.storage.items) b=\(b.storage.items) 共享=\(a.storage === b.storage)（引用成员浅拷贝）"
)

struct DraftValue {
    var items: [String] = []
}

var x = DraftValue(items: ["A1"])
var y = x
y.items.append("B1")
print("struct 值语义: x=\(x.items) y=\(y.items)（独立副本，赋值即 Prototype）")

final class Doc: NSCopying {
    var tags: [String]
    init(tags: [String]) { self.tags = tags }
    func copy(with zone: NSZone? = nil) -> Any { Doc(tags: tags) }
}

let d1 = Doc(tags: ["a"])
let d2 = d1.copy() as! Doc
d2.tags.append("b")
print("class 深拷贝: d1=\(d1.tags) d2=\(d2.tags)（手写 NSCopying/copy 才有独立副本）")
print("结论：struct 赋值语义上就是 Prototype；class 场景要手写深拷贝")
