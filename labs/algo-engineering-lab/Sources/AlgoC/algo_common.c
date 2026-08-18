#include "algo_common.h"

/* 库版本：与 Package / pyproject 的 0.1.0 对齐，便于联调时一眼确认链到的是哪一版。 */
int algo_version(int *out_major, int *out_minor, int *out_patch) {
    if (out_major == NULL || out_minor == NULL || out_patch == NULL) {
        return ALGO_ERR_NULL_POINTER;
    }
    *out_major = 0;
    *out_minor = 1;
    *out_patch = 0;
    return ALGO_OK;
}
