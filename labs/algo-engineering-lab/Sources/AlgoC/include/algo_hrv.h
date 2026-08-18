#ifndef ALGO_HRV_H
#define ALGO_HRV_H

#include "algo_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * HRV 时域指标（单位：RR 为 ms）。
 *
 * 口径见 docs/02-算法对齐口径/hrv-time-domain.md：
 * - SDNN / RMSSD 分母为 N-1（样本统计）
 * - 中间累加用 double，降低 float 截断误差
 * - 不做伪差校正
 *
 * @param rr_ms  调用方持有的 RR 数组（ms）
 * @param count  长度；0 → EMPTY；1 → TOO_SHORT
 * @param out_*  调用方预分配的输出；成功时写入
 */
int algo_hrv_time_domain(
    const double *rr_ms,
    size_t count,
    double *out_sdnn_ms,
    double *out_rmssd_ms,
    double *out_pnn50,
    double *out_mean_rr_ms
);

/* 频域 API 见 algo_hrv_freq.h（保持时域头文件职责单一） */

#ifdef __cplusplus
}
#endif

#endif /* ALGO_HRV_H */
