// T6-Q3 收束报告 Markdown
import Foundation

let report = """
# CoreML 收束报告（示例）

## 1. 问题与契约
- 问题: 二分类玩具特征 (x,y) → pos/neg
- 输入: double x,y
- 输出: classLabel

## 2. 流水线
数据合成 → CreateML MLClassifier → 导出 mlmodel → compile → prediction

## 3. 度量
- 环境: macOS CLI / cpuOnly
- 说明: 未宣称 ANE SLA

## 4. 边界账
端侧默认；无云依赖；体积可忽略

## 5. 回滚
保留上一版 mlmodelc；指标跌破则切回

## 6. 已知缺口
未做真机 ANE；未做分布外样本测试
"""

print(report)
