// T1-Q2 手写 CoW 容器（学员第一版，挂载体 1.2）
// 要点：存储盒必须是 class；写路径在"修改之前"判定独占，不独占先拷贝再改
final class Box<T> {
    var storage: [T] = []
    init(_ s: [T]) { storage = s }
}

// 撞墙记录：第一版把 copyCount 写成 MyArray<T> 的 static 存储属性，
// 编译器报 "static stored properties not supported in generic types"——改用全局计数器。
var cowCopyCount = 0 // 记录真实拷贝次数，当证据用

struct MyArray<T> {
    private var box: Box<T>

    init(_ elements: [T]) { box = Box(elements) }

    var elements: [T] { box.storage }
    var count: Int { box.storage.count }

    // 写路径：判定必须在改之前——先改了就无法判断是否独占了
    private mutating func ensureUnique() {
        if !isKnownUniquelyReferenced(&box) {
            box = Box(box.storage) // 真拷贝发生在这里
            cowCopyCount += 1
        }
    }

    mutating func append(_ element: T) {
        ensureUnique()
        box.storage.append(element)
    }
}

// ---- 验证：赋值廉价（共享盒子），写时才拷贝 ----
var m1 = MyArray<Int>([1, 2, 3])
var m2 = m1 // 只拷了引用字段，盒子共享

print("赋值后 copyCount =", cowCopyCount, "（预期 0：赋值不拷贝）")

m2.append(4) // 只有 m2 写 → 触发一次拷贝
print("m2 写入后 copyCount =", cowCopyCount, "（预期 1：写时拷贝）")
print("m1 =", m1.elements, "| m2 =", m2.elements, "（预期 m1 不受影响）")
assert(m1.elements == [1, 2, 3] && m2.elements == [1, 2, 3, 4], "值语义必须独立")

m1.append(0) // m1 再写：此刻 m1 独占盒子了吗？m1 的 box 还是原来那个（m2 拷走了新的）
print("m1 写入后 copyCount =", cowCopyCount, "（预期仍为 1：m1 已独占旧盒，无需再拷）")
assert(cowCopyCount == 1, "独占时不应重复拷贝")
print("Q2 验证通过：赋值廉价 + 写时拷贝 + 独占免拷")
