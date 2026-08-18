// T4-Q2 NLTagger 优先于自定义 CoreML
import Foundation
import NaturalLanguage

let text = "CoreML 让模型在 iPhone 上离线运行。"
let tagger = NLTagger(tagSchemes: [.lexicalClass, .language])
tagger.string = text

print("语言: \(tagger.tag(at: text.startIndex, unit: .word, scheme: .language).0?.rawValue ?? "?")")
tagger.enumerateTags(in: text.startIndex..<text.endIndex, unit: .word, scheme: .lexicalClass) { tag, range in
    let token = String(text[range])
    print("  \(token) → \(tag?.rawValue ?? "?")")
    return true
}
print(
    """

    记账: 问题=中文分词/词性；约束=无垂直标签、要系统级质量
    决策=先 NLTagger（语言内建）；出现垂直实体/自定义标签再上 CoreML
    """
)
