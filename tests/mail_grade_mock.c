#include "mail/grade.h"

static unsigned int memory[(AF_MAIL_CHECK_BYTES+AF_MAIL_CHECK_RELOC_BYTES)/4];
unsigned int af_grade_allocated, af_grade_freed, af_grade_loaded, af_grade_invoked;
unsigned int af_grade_allocation_size;
int af_grade_fail_allocate, af_grade_wrong_overlay;
void *af_grade_test_allocate(unsigned int size) {
    ++af_grade_allocated;
    af_grade_allocation_size = size;
    return af_grade_fail_allocate ? 0 : memory;
}
void af_grade_test_release(void *p) { if (p == memory) ++af_grade_freed; }
void af_grade_test_load(void *p) {
    unsigned int *header = p;
    ++af_grade_loaded;
    header[4] = af_grade_wrong_overlay ? 0 : AF_MAIL_CHECK_MAGIC;
    header[5] = 1; header[6] = 96; header[7] = AF_MAIL_GRADE_MAX;
}
int af_grade_test_invoke(void *p, AfMailGrade *out, const unsigned char *body, unsigned int size) {
    if (p != memory) return 0;
    ++af_grade_invoked;
    return af_mail_grade(out,body,size);
}
