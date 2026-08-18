#include "algo_fir.h"

#include <math.h>

/*
 * numpy.convolve(a, v, mode='same') 对「full 卷积」取中心长度为 len(a) 的一段。
 * full[i] = sum_k a[k] * v[i-k]（越界为 0），中心起点 = (len(v)-1)//2。
 * 这里令信号为 x、核为 b，与 Python 侧 np.convolve(x, coeffs, mode='same') 一致。
 */
int algo_fir_filter_naive(
    const double *x,
    size_t x_len,
    const double *b,
    size_t b_len,
    double *y,
    size_t y_len
) {
    if (x == NULL || b == NULL || y == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (x_len == 0) {
        return ALGO_ERR_EMPTY;
    }
    if (b_len == 0 || y_len != x_len) {
        return ALGO_ERR_INVALID_ARG;
    }

    for (size_t i = 0; i < x_len; i++) {
        if (!isfinite(x[i])) {
            return ALGO_ERR_NON_FINITE;
        }
    }
    for (size_t k = 0; k < b_len; k++) {
        if (!isfinite(b[k])) {
            return ALGO_ERR_NON_FINITE;
        }
    }

    /* full 卷积长度 = x_len + b_len - 1；same 从 start 开始取 x_len 个点 */
    const size_t start = (b_len - 1) / 2;

    for (size_t n = 0; n < x_len; n++) {
        const size_t full_index = n + start;
        double acc = 0.0;
        for (size_t k = 0; k < b_len; k++) {
            /* full[full_index] 贡献项：x[j] * b[full_index - j]，j∈[0,x_len)
             * 等价：j = full_index - k → 需要 x[full_index - k] * b[k]
             */
            if (full_index >= k) {
                const size_t j = full_index - k;
                if (j < x_len) {
                    acc += x[j] * b[k];
                }
            }
        }
        y[n] = acc;
    }

    return ALGO_OK;
}
