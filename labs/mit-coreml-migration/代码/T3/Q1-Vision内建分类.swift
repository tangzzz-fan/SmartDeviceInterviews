// T3-Q1 Vision 内建分类（程序化图片）
import Foundation
import Vision
import CoreGraphics
import AppKit

func makeSwatch(color: NSColor, size: Int = 224) -> CGImage {
    let image = NSImage(size: NSSize(width: size, height: size))
    image.lockFocus()
    color.setFill()
    NSBezierPath(rect: NSRect(x: 0, y: 0, width: size, height: size)).fill()
    image.unlockFocus()
    var rect = NSRect(origin: .zero, size: image.size)
    return image.cgImage(forProposedRect: &rect, context: nil, hints: nil)!
}

let cgImage = makeSwatch(color: .systemGreen)
let request = VNClassifyImageRequest()
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

let results = (request.results ?? []).prefix(3)
print("Top3:")
for (i, r) in results.enumerated() {
    print("  \(i + 1). \(r.identifier)  \(String(format: "%.3f", r.confidence))")
}
print("说明: 纯色块分类不准是预期——本任务验证管线可跑，不验证语义准头")
