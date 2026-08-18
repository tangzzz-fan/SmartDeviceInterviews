#include "algo_fir_stream.h"

#include <math.h>
#include <string.h>

int algo_fir_stream_reset(AlgoFIRStreamState *state) {
    if (state == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    memset(state->delay, 0, sizeof(state->delay));
    state->taps = ALGO_FIR_NUM_TAPS;
    return ALGO_OK;
}

int algo_fir_stream_process(
    AlgoFIRStreamState *state,
    const double *b,
    size_t b_len,
    const double *x,
    size_t x_len,
    double *y,
    size_t y_len
) {
    if (state == NULL || b == NULL || x == NULL || y == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    if (x_len == 0) {
        return ALGO_ERR_EMPTY;
    }
    if (y_len < x_len) {
        return ALGO_ERR_INVALID_ARG;
    }
    if (state->taps == 0) {
        state->taps = ALGO_FIR_NUM_TAPS;
    }
    if (b_len != state->taps || b_len > ALGO_FIR_NUM_TAPS) {
        return ALGO_ERR_INVALID_ARG;
    }
    for (size_t i = 0; i < x_len; i++) {
        if (!isfinite(x[i])) {
            return ALGO_ERR_NON_FINITE;
        }
    }

    const size_t m = state->taps;
    for (size_t n = 0; n < x_len; n++) {
        /* 延迟线右移：最老的从末端掉落 */
        for (size_t k = m; k-- > 1; ) {
            state->delay[k] = state->delay[k - 1];
        }
        state->delay[0] = x[n];

        double acc = 0.0;
        for (size_t k = 0; k < m; k++) {
            acc += b[k] * state->delay[k];
        }
        y[n] = acc;
    }
    return ALGO_OK;
}
