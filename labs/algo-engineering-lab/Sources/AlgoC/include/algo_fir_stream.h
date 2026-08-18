#ifndef ALGO_FIR_STREAM_H
#define ALGO_FIR_STREAM_H

#include "algo_common.h"
#include "algo_fir_coeffs.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * 因果 FIR 流式状态（延迟线）。
 * 口径：docs/02-算法对齐口径/streaming-fir.md
 * y[n] = sum_k b[k] * x[n-k]；跨窗必须复用同一 state，禁止每窗 reset。
 *
 * delay[0] = 最新样本，delay[M-1] = 最老。
 */
typedef struct AlgoFIRStreamState {
    double delay[ALGO_FIR_NUM_TAPS];
    size_t taps;
} AlgoFIRStreamState;

/** 清零延迟线（仅开流时调用一次；窗边界禁止调用）。 */
int algo_fir_stream_reset(AlgoFIRStreamState *state);

/**
 * 喂入一批新样本，写出等长滤波结果；就地更新 delay。
 * @param b  通常 ALGO_FIR_BANDPASS_COEFFS；b_len 必须 == state->taps
 */
int algo_fir_stream_process(
    AlgoFIRStreamState *state,
    const double *b,
    size_t b_len,
    const double *x,
    size_t x_len,
    double *y,
    size_t y_len
);

#ifdef __cplusplus
}
#endif

#endif /* ALGO_FIR_STREAM_H */
