// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AlgoEngineeringLab",
    platforms: [
        .macOS(.v13),
        .iOS(.v16),
    ],
    products: [
        .library(name: "AlgoSwift", targets: ["AlgoSwift"]),
        .library(name: "AlgoC", targets: ["AlgoC"]),
    ],
    targets: [
        .target(
            name: "AlgoC",
            path: "Sources/AlgoC",
            publicHeadersPath: "include"
        ),
        .target(
            name: "AlgoSwift",
            dependencies: ["AlgoC"],
            path: "Sources/AlgoSwift"
        ),
        .testTarget(
            name: "ParityTests",
            dependencies: ["AlgoSwift", "AlgoC"],
            path: "Tests/ParityTests"
        ),
        .testTarget(
            name: "BenchmarkTests",
            dependencies: ["AlgoSwift", "AlgoC"],
            path: "Tests/BenchmarkTests"
        ),
    ]
)
