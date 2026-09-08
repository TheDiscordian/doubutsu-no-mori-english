#include "../overlays/mail_generation/fortune_slip.h"

unsigned int af_fortune_test_work_size(void) { return sizeof(AfFortuneSlipWork); }
unsigned int af_fortune_test_text_offset(void) {
    return __builtin_offsetof(AfFortuneSlipWork,generation) +
        __builtin_offsetof(AfMailGenerateWork,text);
}
