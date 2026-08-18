#ifndef ALGO_FIR_H
#define ALGO_FIR_H

#include "algo_common.h"
#include "algo_fir_coeffs.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Naive FIR 卷积（直接型），口径 mode='same'：
 * 输出长度 = 输入长度；x 下标越界视为 0。
 *
 * y[n] = sum_{k=0}^{M-1} b[k] * x[n - k + delay]
 * 其中 delay = (M-1)/2，使 same 对齐与 numpy.convolve(..., mode="same") 一致
 *（对奇数长度核，numpy same 取 full 结果的中心段）。
 *
 * @param x / x_len  输入信号（调用方持有）
 * @param b / b_len  系数；通常传 ALGO_FIR_BANDPASS_COEFFS / ALGO_FIR_NUM_TAPS
 * @param y / y_len  输出缓冲，y_len 必须等于 x_len
 */
int algo_fir_filter_naive(
    const double *x,
    size_t x_len,
    const double *b,
    size_t b_len,
    double *y,
    size_t y_len
);

#ifdef __cplusplus
}
#endif

#endif /* ALGO_FIR_H */
