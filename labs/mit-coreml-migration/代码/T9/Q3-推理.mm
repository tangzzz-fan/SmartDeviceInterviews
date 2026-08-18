// T9-Q3 C++（ObjC++ 桥）加载 .mlmodelc 并推理（参考解法）
// 编译: clang++ -x objective-c++ -std=c++17 -fobjc-arc -framework CoreML -framework Foundation -o .artifacts/infer Q3-推理.mm
#import <CoreML/CoreML.h>
#import <Foundation/Foundation.h>
#include <iostream>

int main(int argc, const char* argv[]) {
    @autoreleasepool {
        NSString* modelPath = argc > 1
            ? [NSString stringWithUTF8String:argv[1]]
            : @"../../T7/.artifacts/model.mlpackage"; // 默认占位
        NSError* err = nil;
        MLModel* model = [MLModel modelWithContentsOfURL:[NSURL fileURLWithPath:modelPath] error:&err];
        if (!model) {
            std::cerr << "加载失败: " << (err ? err.description.UTF8String : "unknown") << "\n";
            return 1;
        }

        // 输入契约: input (1, 4) float32
        MLMultiArray* arr = [[MLMultiArray alloc] initWithShape:@[@1, @4]
                                                       dataType:MLMultiArrayDataTypeFloat32
                                                          error:&err];
        if (!arr) { std::cerr << "MultiArray 失败: " << err.description.UTF8String << "\n"; return 1; }
        float* data = (float*)arr.dataPointer;
        double input[4] = {0.2, -0.3, 0.5, 0.8};
        for (int i = 0; i < 4; i++) data[i] = (float)input[i];

        MLDictionaryFeatureProvider* provider = [[MLDictionaryFeatureProvider alloc] initWithDictionary:@{@"input": arr} error:&err];
        if (!provider) { std::cerr << "输入构造失败: " << err.description.UTF8String << "\n"; return 1; }

        MLPredictionOptions* opts = [[MLPredictionOptions alloc] init];
        id<MLFeatureProvider> out = [model predictionFromFeatures:provider options:opts error:&err];
        if (!out) {
            std::cerr << "推理失败: " << (err ? err.description.UTF8String : "unknown") << "\n";
            return 1;
        }
        MLMultiArray* res = [out featureValueForName:@"output"].multiArrayValue;
        float* od = (float*)res.dataPointer;
        double maxv = od[0]; int argmax = 0;
        for (int i = 1; i < 3; i++) if (od[i] > maxv) { maxv = od[i]; argmax = i; }
        std::cout << "C++ 输出: [" << od[0] << ", " << od[1] << ", " << od[2] << "] argmax=" << argmax << "\n";
    }
    return 0;
}
