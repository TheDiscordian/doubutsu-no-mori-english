#include "../overlays/mail_generation/generate.h"

unsigned int af_mail_capture_size(void) { return sizeof(AfMailCapture); }
unsigned int af_mail_selection_size(void) { return sizeof(AfMailSelection); }
unsigned int af_mail_generate_work_size(void) { return sizeof(AfMailGenerateWork); }
unsigned int af_mail_generate_text_offset(void) {
    return __builtin_offsetof(AfMailGenerateWork,text);
}
