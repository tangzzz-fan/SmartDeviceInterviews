// T2-Q4 Prototype 深拷贝：class 含引用成员
import Foundation

final class Author {
    var name: String
    init(_ name: String) { self.name = name }
}

final class Book {
    var title: String
    var author: Author

    init(_ title: String, _ author: Author) {
        self.title = title
        self.author = author
    }

    func deepCopy() -> Book {
        Book(title, Author(author.name))
    }
}

let author = Author("张三")
let original = Book("Swift 模式", author)

let shallow = Book(original.title, original.author)
shallow.author.name = "李四"
print("浅拷贝: original.author=\(original.author.name)（被连坐，引用成员共享）")

let deep = original.deepCopy()
deep.author.name = "王五"
print("深拷贝: original.author=\(original.author.name)（独立）")
print("结论: struct 包 class 成员时拷贝的仍是引用；class 场景要递归深拷贝，值语义只对纯值类型免费")
