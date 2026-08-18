#include "algo_hrv.h"

#include <math.h>

int algo_hrv_time_domain(
    const double *rr_ms,
    size_t count,
    double *out_sdnn_ms,
    double *out_rmssd_ms,
    double *out_pnn50,
    double *out_mean_rr_ms
) {
    /* 指针契约：输入与全部输出指针都必须有效（见 docs/04） */
    if (rr_ms == NULL || out_sdnn_ms == NULL || out_rmssd_ms == NULL
        || out_pnn50 == NULL || out_mean_rr_ms == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (count == 0) {
        return ALGO_ERR_EMPTY;
    }
    if (count < 2) {
        return ALGO_ERR_TOO_SHORT;
    }

    /* 先扫一遍非有限值，避免算出「看起来合法」的垃圾指标 */
    for (size_t i = 0; i < count; i++) {
        if (!isfinite(rr_ms[i])) {
            return ALGO_ERR_NON_FINITE;
        }
    }

    double sum = 0.0;
    for (size_t i = 0; i < count; i++) {
        sum += rr_ms[i];
    }
    const double mean = sum / (double)count;

    /* SDNN：sqrt( sum((x-mean)^2) / (N-1) ) */
    double acc = 0.0;
    for (size_t i = 0; i < count; i++) {
        const double d = rr_ms[i] - mean;
        acc += d * d;
    }
    const double sdnn = sqrt(acc / (double)(count - 1));

    /* RMSSD：相邻差分 */
    double acc_diff = 0.0;
    size_t over50 = 0;
    const size_t n_diff = count - 1;
    for (size_t i = 0; i < n_diff; i++) {
        const double diff = rr_ms[i + 1] - rr_ms[i];
        acc_diff += diff * diff;
        if (fabs(diff) > 50.0) {
            over50++;
        }
    }
    const double rmssd = sqrt(acc_diff / (double)n_diff);
    const double pnn50 = 100.0 * ((double)over50 / (double)n_diff);

    *out_sdnn_ms = sdnn;
    *out_rmssd_ms = rmssd;
    *out_pnn50 = pnn50;
    *out_mean_rr_ms = mean;
    return ALGO_OK;
}
