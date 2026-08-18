// T3-Q4 协议组合 vs 继承对拍
// 同一需求：数据源 + 缓存 + 日志 + 校验；两版实现后量化对比。
import Foundation

protocol DataSource {
    func load() -> [String]
}

// MARK: - 继承版：能力靠子类叠，每多一种能力就多一层类型身份

class BaseDataSource: DataSource {
    func load() -> [String] { [] }
}

class FileDataSource: BaseDataSource {
    override func load() -> [String] { ["file1", "file2"] }
}

/// 继承版加缓存：必须再开一个子类，且只能挂在 File 这条枝上
class CachedFileDataSource: FileDataSource {
    private var cached: [String]?
    override func load() -> [String] {
        if let cached { print("继承版缓存命中"); return cached }
        let items = super.load()
        cached = items
        print("继承版缓存写入 \(items.count) 条")
        return items
    }
}

/// 再加日志：又要开子类；想「Remote + 缓存 + 日志」就得再开一枝树
class LoggedCachedFileDataSource: CachedFileDataSource {
    override func load() -> [String] {
        print("继承版日志: 开始 load")
        let items = super.load()
        print("继承版日志: 结束 load (\(items.count))")
        return items
    }
}

// MARK: - 组合版：同一协议上递归包装，能力任意叠加、任意替换

struct RemoteSource: DataSource {
    func load() -> [String] { ["remote1", "remote2"] }
}

struct ValidatedSource: DataSource {
    let wrapped: DataSource
    func load() -> [String] {
        let items = wrapped.load().filter { !$0.isEmpty }
        print("组合版校验: 保留 \(items.count) 条非空")
        return items
    }
}

struct CachedSource: DataSource {
    let wrapped: DataSource
    private let box = CacheBox()

    init(wrapped: DataSource) {
        self.wrapped = wrapped
    }

    func load() -> [String] {
        if let hit = box.value {
            print("组合版缓存命中")
            return hit
        }
        let items = wrapped.load()
        box.value = items
        print("组合版缓存写入 \(items.count) 条")
        return items
    }
}

/// class 盒子：让 struct 包装器也能持有可变缓存
final class CacheBox {
    var value: [String]?
}

struct LoggedSource: DataSource {
    let wrapped: DataSource
    func load() -> [String] {
        print("组合版日志: 开始 load")
        let items = wrapped.load()
        print("组合版日志: 结束 load (\(items.count))")
        return items
    }
}

// MARK: - 对拍演示

print("=== 继承版（File → Cached → Logged）===")
let inherited: DataSource = LoggedCachedFileDataSource()
_ = inherited.load()
_ = inherited.load() // 第二次应命中缓存

print("\n=== 组合版（Logged > Cached > Validated > Remote）===")
let composed: DataSource = LoggedSource(
    wrapped: CachedSource(
        wrapped: ValidatedSource(wrapped: RemoteSource())
    )
)
_ = composed.load()
_ = composed.load()

print(
    """

    量化对比:
      继承版类型数 = 4（Base/File/CachedFile/LoggedCachedFile）；加「Remote+缓存」要再开平行枝
      组合版类型数 = 1 协议 + 4 包装（Remote/Validated/Cached/Logged）；任意排列组合
      修改点: 继承版改能力=动继承树；组合版改能力=换一层包装
      可替换性: 组合版任意 DataSource 可被包装；继承版能力绑死在 File 身份上

    结论: 行为可叠加/可替换 → 协议组合优先；is-a 身份（框架回调）时继承仍合理
    """
)
