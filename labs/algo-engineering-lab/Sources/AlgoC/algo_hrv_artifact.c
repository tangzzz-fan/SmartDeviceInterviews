#include "algo_hrv_artifact.h"

#include <math.h>
#include <stddef.h>

static double local_median(const double *x, size_t n, size_t i) {
    double neighbors[4];
    size_t m = 0;
    if (i >= 2) neighbors[m++] = x[i - 2];
    if (i >= 1) neighbors[m++] = x[i - 1];
    if (i + 1 < n) neighbors[m++] = x[i + 1];
    if (i + 2 < n) neighbors[m++] = x[i + 2];
    if (m == 0) {
        return x[i];
    }

    /* m 最多 4，简单排序足够。 */
    for (size_t a = 0; a < m; a++) {
        for (size_t b = a + 1; b < m; b++) {
            if (neighbors[b] < neighbors[a]) {
                const double t = neighbors[a];
                neighbors[a] = neighbors[b];
                neighbors[b] = t;
            }
        }
    }
    if (m % 2 == 1) {
        return neighbors[m / 2];
    }
    return 0.5 * (neighbors[m / 2 - 1] + neighbors[m / 2]);
}

int algo_hrv_correct_artifacts(
    const double *rr_ms,
    size_t count,
    double threshold_ms,
    double *out_corrected,
    uint8_t *out_mask
) {
    if (rr_ms == NULL || out_corrected == NULL || out_mask == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (count == 0) {
        return ALGO_ERR_EMPTY;
    }
    if (count < 2) {
        return ALGO_ERR_TOO_SHORT;
    }
    if (!(threshold_ms > 0.0) || !isfinite(threshold_ms)) {
        return ALGO_ERR_INVALID_ARG;
    }

    for (size_t i = 0; i < count; i++) {
        if (!isfinite(rr_ms[i])) {
            return ALGO_ERR_NON_FINITE;
        }
        out_corrected[i] = rr_ms[i];
        out_mask[i] = 0;
    }

    for (size_t i = 0; i < count; i++) {
        const double rr = rr_ms[i];
        if (rr < 300.0 || rr > 2000.0) {
            out_mask[i] = 1;
            continue;
        }
        const double med = local_median(rr_ms, count, i);
        if (fabs(rr - med) > threshold_ms) {
            out_mask[i] = 1;
        }
    }

    for (size_t i = 0; i < count; i++) {
        if (out_mask[i] == 0) {
            continue;
        }
        ptrdiff_t left = (ptrdiff_t)i - 1;
        while (left >= 0 && out_mask[(size_t)left] == 1) {
            left--;
        }
        size_t right = i + 1;
        while (right < count && out_mask[right] == 1) {
            right++;
        }

        if (left >= 0 && right < count) {
            const double t = (double)((ptrdiff_t)i - left) / (double)((ptrdiff_t)right - left);
            out_corrected[i] = out_corrected[(size_t)left] + t * (out_corrected[right] - out_corrected[(size_t)left]);
        } else if (left >= 0) {
            out_corrected[i] = out_corrected[(size_t)left];
        } else if (right < count) {
            out_corrected[i] = out_corrected[right];
        } else {
            out_corrected[i] = rr_ms[i];
        }
    }

    return ALGO_OK;
}
