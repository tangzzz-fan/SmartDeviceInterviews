// T5-Q1 MVVM 小工程（CLI 演示：ViewModel 可脱离 View 测试）
import Foundation
import Observation

@Observable
final class SearchViewModel {
    var query = ""
    var results: [String] = []
    var isSearching = false
    func search() {
        guard !query.isEmpty else { results = []; return }
        isSearching = true
        results = ["结果A(" + query + ")", "结果B(" + query + ")"]
        isSearching = false
    }
}

// 可脱离 View 测试
let vm = SearchViewModel()
vm.query = "swift"
vm.search()
print("ViewModel 状态: query=\(vm.query) results=\(vm.results) isSearching=\(vm.isSearching)")
print("朴素版: 状态全在 View、逻辑不可测；MVVM 版: ViewModel 承载状态+逻辑，测试直接 new SearchViewModel()")
print("说明: SwiftUI View 部分（@State 绑定 body）需真机/Xcode 验证，CLI 只验证可测的 ViewModel 层")
