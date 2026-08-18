#ifndef ALGO_HRV_ARTIFACT_H
#define ALGO_HRV_ARTIFACT_H

#include <stdint.h>

#include "algo_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * HRV 伪差校正：局部中位数偏差阈值 + 生理范围约束。
 *
 * @param rr_ms          输入 RR（ms）
 * @param count          输入长度；0->EMPTY；1->TOO_SHORT
 * @param threshold_ms   偏差阈值（建议 120ms）
 * @param out_corrected  输出校正后 RR，长度 >= count
 * @param out_mask       输出伪差掩码（0/1），长度 >= count
 */
int algo_hrv_correct_artifacts(
    const double *rr_ms,
    size_t count,
    double threshold_ms,
    double *out_corrected,
    uint8_t *out_mask
);

#ifdef __cplusplus
}
#endif

#endif /* ALGO_HRV_ARTIFACT_H */
