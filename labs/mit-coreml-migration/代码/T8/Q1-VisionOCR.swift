// T8-Q1 Vision OCR 可跑代理（Live Text 底层能力的 CLI 版）
import AppKit
import Vision

let width = 420, height = 120
guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
) else { fatalError("无法创建位图") }

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()
let attrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 34),
    .foregroundColor: NSColor.black,
]
("Hello CoreML 2026" as NSString).draw(at: NSPoint(x: 20, y: 42), withAttributes: attrs)
NSGraphicsContext.restoreGraphicsState()

let cg = rep.cgImage!

let request = VNRecognizeTextRequest { req, err in
    if let err { print("识别错误:", err.localizedDescription); return }
    for obs in (req.results as? [VNRecognizedTextObservation]) ?? [] {
        if let top = obs.topCandidates(1).first {
            print(String(format: "文本: %@  置信度: %.2f", top.string, top.confidence))
        }
    }
}
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
try? VNImageRequestHandler(cgImage: cg).perform([request])
print("说明: VNRecognizeTextRequest 是 VisionKit Live Text 的底层能力；ImageAnalyzer 在此基础上加交互层（待真机/App 环境）。")
