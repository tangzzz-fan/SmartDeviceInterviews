#include "algo_hrv_freq.h"

#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static double lerp_interp(double x, const double *xp, const double *fp, size_t n) {
    /* 与 numpy.interp 边界行为一致：夹到端点 */
    if (x <= xp[0]) {
        return fp[0];
    }
    if (x >= xp[n - 1]) {
        return fp[n - 1];
    }
    size_t lo = 0;
    size_t hi = n - 1;
    while (hi - lo > 1) {
        size_t mid = lo + (hi - lo) / 2;
        if (xp[mid] <= x) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    const double dx = xp[hi] - xp[lo];
    if (dx == 0.0) {
        return fp[lo];
    }
    const double t = (x - xp[lo]) / dx;
    return fp[lo] + t * (fp[hi] - fp[lo]);
}

static void hann_window(double *w, size_t n) {
    if (n == 1) {
        w[0] = 1.0;
        return;
    }
    for (size_t i = 0; i < n; i++) {
        w[i] = 0.5 - 0.5 * cos(2.0 * M_PI * (double)i / (double)(n - 1));
    }
}

/* 朴素 rFFT：X[k]=sum x[n] exp(-2πi kn/N)，k=0..N/2；与 numpy.fft.rfft 同定义（无 1/N） */
static void rfft_power(
    const double *x,
    size_t n,
    double *out_psd,
    double *out_freqs,
    size_t n_psd
) {
    const double inv_n2 = 1.0 / ((double)n * (double)n);
    for (size_t k = 0; k < n_psd; k++) {
        double re = 0.0;
        double im = 0.0;
        const double ang0 = -2.0 * M_PI * (double)k / (double)n;
        for (size_t j = 0; j < n; j++) {
            const double ang = ang0 * (double)j;
            re += x[j] * cos(ang);
            im += x[j] * sin(ang);
        }
        out_psd[k] = (re * re + im * im) * inv_n2;
        out_freqs[k] = (double)k * ALGO_HRV_FREQ_FS / (double)n;
    }
}

/* numpy.trapezoid(y, x) */
static double trapezoid(const double *y, const double *x, size_t n) {
    if (n == 0) {
        return 0.0;
    }
    if (n == 1) {
        return 0.0; /* 调用方对单点另处理 */
    }
    double acc = 0.0;
    for (size_t i = 0; i + 1 < n; i++) {
        acc += (x[i + 1] - x[i]) * (y[i] + y[i + 1]) * 0.5;
    }
    return acc;
}

static double band_power(
    const double *psd,
    const double *freqs,
    size_t n_psd,
    double lo,
    double hi,
    int hi_inclusive
) {
    /* 收集落在频带内的点；单点时用 Δf≈freqs[1]-freqs[0] 矩形近似（与 Python 一致） */
    double f_buf[ALGO_HRV_FREQ_MAX_PSD];
    double p_buf[ALGO_HRV_FREQ_MAX_PSD];
    size_t m = 0;
    for (size_t i = 0; i < n_psd; i++) {
        const double f = freqs[i];
        int ok = 0;
        if (hi_inclusive) {
            ok = (f >= lo && f <= hi);
        } else {
            ok = (f >= lo && f < hi);
        }
        if (ok) {
            f_buf[m] = f;
            p_buf[m] = psd[i];
            m++;
        }
    }
    if (m == 0) {
        return 0.0;
    }
    if (m == 1) {
        const double df = (n_psd > 1) ? (freqs[1] - freqs[0]) : 0.0;
        return p_buf[0] * df;
    }
    return trapezoid(p_buf, f_buf, m);
}

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
) {
    if (rr_ms == NULL || out_lf == NULL || out_hf == NULL || out_lf_hf_ratio == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (count == 0) {
        return ALGO_ERR_EMPTY;
    }
    if (count < ALGO_HRV_FREQ_MIN_RR) {
        return ALGO_ERR_TOO_SHORT;
    }
    for (size_t i = 0; i < count; i++) {
        if (!isfinite(rr_ms[i])) {
            return ALGO_ERR_NON_FINITE;
        }
    }

    /* 时间轴：t0=0，ti = t{i-1} + RR{i-1}/1000 */
    double t_axis[ALGO_HRV_FREQ_MAX_TIME];
    if (count > ALGO_HRV_FREQ_MAX_TIME) {
        return ALGO_ERR_INVALID_ARG;
    }
    t_axis[0] = 0.0;
    for (size_t i = 1; i < count; i++) {
        t_axis[i] = t_axis[i - 1] + rr_ms[i - 1] / 1000.0;
    }
    const double duration = t_axis[count - 1];
    if (!(duration > 0.0)) {
        return ALGO_ERR_INVALID_ARG;
    }

    /* 4Hz 均匀网格，不超过 duration */
    size_t n_out = (size_t)(duration * ALGO_HRV_FREQ_FS) + 1;
    if (n_out > ALGO_HRV_FREQ_MAX_TIME) {
        return ALGO_ERR_INVALID_ARG;
    }
    while (n_out > 0 && ((double)(n_out - 1) / ALGO_HRV_FREQ_FS) > duration + 1e-12) {
        n_out--;
    }
    if (n_out < 2) {
        return ALGO_ERR_TOO_SHORT;
    }

    double resampled[ALGO_HRV_FREQ_MAX_TIME];
    double detrended[ALGO_HRV_FREQ_MAX_TIME];
    double windowed[ALGO_HRV_FREQ_MAX_TIME];
    double win[ALGO_HRV_FREQ_MAX_TIME];
    double psd[ALGO_HRV_FREQ_MAX_PSD];
    double freqs[ALGO_HRV_FREQ_MAX_PSD];

    for (size_t i = 0; i < n_out; i++) {
        const double tu = (double)i / ALGO_HRV_FREQ_FS;
        resampled[i] = lerp_interp(tu, t_axis, rr_ms, count);
    }

    double mean = 0.0;
    for (size_t i = 0; i < n_out; i++) {
        mean += resampled[i];
    }
    mean /= (double)n_out;
    for (size_t i = 0; i < n_out; i++) {
        detrended[i] = resampled[i] - mean;
    }

    hann_window(win, n_out);
    for (size_t i = 0; i < n_out; i++) {
        windowed[i] = detrended[i] * win[i];
    }

    const size_t n_psd = n_out / 2 + 1;
    rfft_power(windowed, n_out, psd, freqs, n_psd);

    /* LF: [0.04, 0.15)；HF: [0.15, 0.40] —— 0.15 只进 HF，避免双计 */
    const double lf = band_power(psd, freqs, n_psd, 0.04, 0.15, 0);
    const double hf = band_power(psd, freqs, n_psd, 0.15, 0.40, 1);
    if (hf == 0.0) {
        return ALGO_ERR_INVALID_ARG;
    }

    *out_lf = lf;
    *out_hf = hf;
    *out_lf_hf_ratio = lf / hf;

    const int want_time = (out_resampled != NULL || out_detrended != NULL || out_windowed != NULL);
    const int want_psd = (out_psd != NULL || out_freqs != NULL);
    if (want_time && inout_n_time == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (want_psd && inout_n_psd == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (want_time && *inout_n_time < n_out) {
        return ALGO_ERR_INVALID_ARG;
    }
    if (want_psd && *inout_n_psd < n_psd) {
        return ALGO_ERR_INVALID_ARG;
    }
    if (inout_n_time != NULL) {
        *inout_n_time = n_out;
    }
    if (inout_n_psd != NULL) {
        *inout_n_psd = n_psd;
    }

    if (out_resampled != NULL) {
        memcpy(out_resampled, resampled, n_out * sizeof(double));
    }
    if (out_detrended != NULL) {
        memcpy(out_detrended, detrended, n_out * sizeof(double));
    }
    if (out_windowed != NULL) {
        memcpy(out_windowed, windowed, n_out * sizeof(double));
    }
    if (out_psd != NULL) {
        memcpy(out_psd, psd, n_psd * sizeof(double));
    }
    if (out_freqs != NULL) {
        memcpy(out_freqs, freqs, n_psd * sizeof(double));
    }

    return ALGO_OK;
}
