/* Load English scoring only on demand, in the original mail-check allocation. */
#include "mail/grade.h"
#include "mail/npc.h"

AfMailNpcContext *af_mail_npc_context;

#ifdef __mips__
static void *allocate(unsigned int size) { return ((void *(*)(unsigned int))0x8009BFC0u)(size); }
static void release(void *memory) { ((void (*)(void *))0x8009C040u)(memory); }
static void load(void *memory) {
    ((void (*)(unsigned int,unsigned int,unsigned int,unsigned int,void *,void *,unsigned int))0x800262D0u)
        (0x00954D30u,0x009563E0u,0x80A94AC0u,0x80A96170u,memory,
         (unsigned char *)memory+AF_MAIL_CHECK_BYTES,AF_MAIL_CHECK_RELOC_BYTES);
}
static int invoke(void *memory, void *output, const unsigned char *body, unsigned int size, unsigned int entry) {
    if (entry)
        return ((int (*)(int *,const unsigned char *,unsigned int))((unsigned char *)memory+8))(output,body,size);
    return ((int (*)(AfMailGrade *,const unsigned char *,unsigned int))memory)(output,body,size);
}
#else
extern void *af_grade_test_allocate(unsigned int);
extern void af_grade_test_release(void *);
extern void af_grade_test_load(void *);
extern int af_grade_test_invoke(void *,AfMailGrade *,const unsigned char *,unsigned int);
extern int af_grade_test_invoke_word(void *,int *,const unsigned char *,unsigned int);
#define allocate af_grade_test_allocate
#define release af_grade_test_release
#define load af_grade_test_load
static int invoke(void *memory, void *output, const unsigned char *body, unsigned int size, unsigned int entry) {
    return entry ? af_grade_test_invoke_word(memory,output,body,size)
                 : af_grade_test_invoke(memory,output,body,size);
}
#endif

static int loaded_call(void *output, const unsigned char *body, unsigned int size, unsigned int entry) {
    unsigned int *memory;
    int result = entry ? -1 : 0;
    if (!output || !body || size > AF_MAIL_GRADE_MAX) return result;
    /* Supply the relocation workspace too, so a second allocation cannot
     * fail inside the native loader after the checked allocation succeeds.
     */
    memory = allocate(AF_MAIL_CHECK_BYTES+AF_MAIL_CHECK_RELOC_BYTES);
    if (!memory) return result;
    load(memory);
    if (memory[4] == AF_MAIL_CHECK_MAGIC && memory[5] == 1 && memory[6] == 96 && memory[7] == AF_MAIL_GRADE_MAX)
        result = invoke(memory,output,body,size,entry);
    release(memory);
    return result;
}

int af_mail_grade_body(AfMailGrade *output, const unsigned char *body, unsigned int size) {
    return loaded_call(output,body,size,0);
}

int af_mail_word_rate_body(int *words, const unsigned char *body, unsigned int size) {
    return loaded_call(words,body,size,8);
}

unsigned int af_mail_grade_native(const unsigned char *body) {
    AfMailGrade output;
    if (af_mail_npc_context && af_mail_npc_context->body == body)
        return af_mail_npc_context->ordinary;
    return af_mail_grade_body(&output,body,96) ? output.rank : 2u;
}
