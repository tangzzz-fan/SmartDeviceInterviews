// T1-Q1 值语义泄漏现形记（学员第一版）
// 思路：struct 包裸 class = 把 OC 的共享语义偷渡进"值类型"
final class Storage {
    var items: [Int] = []
}

struct Wrapper {
    var box: Storage
}

var a = Wrapper(box: Storage())
a.box.items.append(1)

var b = a              // struct 逐字段拷贝：拷的是 box 这个"引用"本身
b.box.items.append(2)  // 改的是堆上同一个 Storage

print("泄漏版 a.items =", a.box.items) // 预期 [1, 2] —— a 被 b 连坐
print("泄漏版 a/b 共享同一存储盒:", a.box === b.box)

// ---- 修复：值化存储（数据本来就是数据，别借宿 class）----
struct WrapperFixed {
    var items: [Int] = [] // Array 自带 CoW，赋值廉价、改时拷贝
}

var x = WrapperFixed()
x.items.append(1)
var y = x
y.items.append(2)
print("修复版 x.items =", x.items, "| y.items =", y.items) // [1] [2]，独立
