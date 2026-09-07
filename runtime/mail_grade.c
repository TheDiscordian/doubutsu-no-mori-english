/* Load English scoring only on demand, in the original mail-check allocation. */
#include "mail/grade.h"

#ifdef __mips__
static void *allocate(unsigned int size) { return ((void *(*)(unsigned int))0x8009BFC0u)(size); }
static void release(void *memory) { ((void (*)(void *))0x8009C040u)(memory); }
static void load(void *memory) {
    ((void (*)(unsigned int,unsigned int,unsigned int,unsigned int,void *,void *,unsigned int))0x800262D0u)
        (0x00954D30u,0x009563E0u,0x80A94AC0u,0x80A96170u,memory,
         (unsigned char *)memory+AF_MAIL_CHECK_BYTES,AF_MAIL_CHECK_RELOC_BYTES);
}
static int invoke(void *memory, AfMailGrade *output, const unsigned char *body, unsigned int size) {
    return ((int (*)(AfMailGrade *,const unsigned char *,unsigned int))memory)(output,body,size);
}
#else
extern void *af_grade_test_allocate(unsigned int);
extern void af_grade_test_release(void *);
extern void af_grade_test_load(void *);
extern int af_grade_test_invoke(void *,AfMailGrade *,const unsigned char *,unsigned int);
#define allocate af_grade_test_allocate
#define release af_grade_test_release
#define load af_grade_test_load
#define invoke af_grade_test_invoke
#endif

int af_mail_grade_body(AfMailGrade *output, const unsigned char *body, unsigned int size) {
    unsigned int *memory;
    int result = 0;
    if (!output || !body || size > AF_MAIL_GRADE_MAX) return 0;
    /* Supply the relocation workspace too, so a second allocation cannot
     * fail inside the native loader after the checked allocation succeeds.
     */
    memory = allocate(AF_MAIL_CHECK_BYTES+AF_MAIL_CHECK_RELOC_BYTES);
    if (!memory) return 0;
    load(memory);
    if (memory[4] == AF_MAIL_CHECK_MAGIC && memory[5] == 1 && memory[6] == 96 && memory[7] == AF_MAIL_GRADE_MAX)
        result = invoke(memory,output,body,size);
    release(memory);
    return result;
}

unsigned int af_mail_grade_native(const unsigned char *body) {
    AfMailGrade output;
    return af_mail_grade_body(&output,body,96) ? output.rank : 2u;
}
