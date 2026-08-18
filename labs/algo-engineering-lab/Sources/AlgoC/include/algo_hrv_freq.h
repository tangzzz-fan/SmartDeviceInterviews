#ifndef ALGO_HRV_FREQ_H
#define ALGO_HRV_FREQ_H

#include "algo_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/** 重采样率与缓冲上限（见 docs/02-算法对齐口径/hrv-freq-domain.md） */
#define ALGO_HRV_FREQ_FS 4.0
#define ALGO_HRV_FREQ_MIN_RR 16
#define ALGO_HRV_FREQ_MAX_TIME 4096
/* 字面量常量：Swift 无法导入带括号表达式的宏 */
#define ALGO_HRV_FREQ_MAX_PSD 2049

/**
 * HRV 频域：RR(ms) → 4Hz 插值 → 减均值 → Hann → rFFT → P=|X|^2/N^2 → LF/HF。
 *
 * 快照缓冲可为 NULL（跳过写入）。非 NULL 时：
 * - out_resampled / detrended / windowed：容量 ≥ ALGO_HRV_FREQ_MAX_TIME
 * - out_psd / out_freqs：容量 ≥ ALGO_HRV_FREQ_MAX_PSD
 * - inout_n_time / inout_n_psd：入参为容量，出参为实际长度
 *
 * HF=0 时返回 ALGO_ERR_INVALID_ARG（无法定义 ratio）。
 */
int algo_hrv_freq_domain(
    const double *rr_ms,
    size_t count,
    double *out_lf,
    double *out_hf,
    double *out_lf_hf_ratio,
    double *out_resampled,
    double *out_detrended,
    double *out_windowed,
    double *out_psd,
    double *out_freqs,
    size_t *inout_n_time,
    size_t *inout_n_psd
);

#ifdef __cplusplus
}
#endif

#endif /* ALGO_HRV_FREQ_H */
