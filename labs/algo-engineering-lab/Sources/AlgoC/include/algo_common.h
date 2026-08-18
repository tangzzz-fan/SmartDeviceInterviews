#ifndef ALGO_COMMON_H
#define ALGO_COMMON_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * 统一错误码（见 docs/04-C库集成规范.md）。
 * C 侧用 int 返回；Swift 侧映射为 AlgoError。
 * 成功必须返回 ALGO_OK，并通过「输出指针」写出结果——不要用特殊魔法数当结果。
 */
enum {
    ALGO_OK = 0,
    ALGO_ERR_EMPTY = 1,        /* 长度为 0 */
    ALGO_ERR_TOO_SHORT = 2,    /* 有数据但不够算该指标 */
    ALGO_ERR_NON_FINITE = 3,   /* 含 NaN / Inf */
    ALGO_ERR_NULL_POINTER = 4, /* 必填指针为 NULL */
    ALGO_ERR_INVALID_ARG = 5   /* 其它非法参数 */
};

/**
 * 冒烟 API：写出语义化版本号，证明 Swift↔C 链路打通。
 * @param out_major/minor/patch 调用方预分配；C 只写入、不释放
 * @return ALGO_OK 或 ALGO_ERR_NULL_POINTER
 */
int algo_version(int *out_major, int *out_minor, int *out_patch);

#ifdef __cplusplus
}
#endif

#endif /* ALGO_COMMON_H */
