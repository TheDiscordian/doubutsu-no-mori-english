/* Decode before sending; native state changes use scoped, complete-body grades. */
#include "mail/npc.h"
#include "mail/grade.h"
#include "mail/reader.h"

typedef struct {
    AfMailWorkspace workspace;
    AfMailText letter;
} Scratch;

#ifdef __mips__
extern int af_mail_send_original(const unsigned char *);
extern unsigned int af_mail_length_original(int *, const unsigned char *);
static void *allocate(unsigned int size) { return ((void *(*)(unsigned int))0x8009BFC0u)(size); }
static void release(void *memory) { ((void (*)(void *))0x8009C040u)(memory); }
#else
extern void *af_npc_test_allocate(unsigned int);
extern void af_npc_test_release(void *);
extern int af_npc_test_send_original(const unsigned char *);
extern unsigned int af_npc_test_length_original(int *, const unsigned char *);
#define allocate af_npc_test_allocate
#define release af_npc_test_release
#define af_mail_send_original af_npc_test_send_original
#define af_mail_length_original af_npc_test_length_original
#endif

static unsigned int length_grade(int *length, const unsigned char *body, unsigned int size,
                                int words, int rate) {
    unsigned int i, previous = ' ', run = 1, repeated = 0;
    *length = 0;
    for (i = 0; i < size; ++i) {
        unsigned int c = body[i], special;
        if (c == ' ') continue;
        ++*length;
        if (repeated) continue;
        if (c == previous) {
            ++run;
            special = c == 0x21u || c == 0x22u || c == 0x5Fu || c == 0x90u || c == 0x5Cu
                || (c >= 0x25u && c <= 0x40u) || (c >= 0x7Fu && c <= 0x85u);
            if (run >= (special ? 8u : 3u)) repeated = 1;
        } else {
            previous = c;
            run = 0;
        }
    }
    return words < 3 ? (*length < 5 || repeated ? 0u : 2u)
                    : rate >= 30 ? 1u : repeated ? 0u : 2u;
}

int af_mail_send_npc(const unsigned char *mail) {
    AfMailNpcContext context, *previous;
    AfMailGrade grade;
    Scratch *scratch;
    void *allocation;
    const unsigned char *body;
    unsigned int size;
    int result, words, rate;
    if (!mail) return 0;
    if (mail[0x27] != AF_MAIL_SNAPSHOT_SPLIT)
        return af_mail_send_original(mail);
    if (mail[0x26] == 255u) return 0;
    allocation = allocate(sizeof(Scratch)+15u);
    if (!allocation) return 0;
    scratch = (Scratch *)(((__UINTPTR_TYPE__)allocation+15u)&~(__UINTPTR_TYPE__)15u);
    result = af_mail_restore(&scratch->letter,mail+0x2A,122,&scratch->workspace);
    if (result) {
        body = scratch->letter.text+scratch->letter.offsets[1];
        size = scratch->letter.lengths[1];
        result = af_mail_grade_body(&grade,body,size);
        if (result) {
            rate = af_mail_word_rate_body(&words,body,size);
            result = rate >= 0;
            if (result) {
                context.body = mail+0x34;
                context.ordinary = grade.rank;
                context.legacy = length_grade(&context.nonspaces,body,size,words,rate);
            }
        }
    }
    release(allocation);
    if (!result) return 0;
    previous = af_mail_npc_context;
    af_mail_npc_context = &context;
    result = af_mail_send_original(mail);
    af_mail_npc_context = previous;
    return result;
}

unsigned int af_mail_grade_length(int *length, const unsigned char *body) {
    if (!length || !body) return 2;
    if (af_mail_npc_context && af_mail_npc_context->body == body) {
        *length = af_mail_npc_context->nonspaces;
        return af_mail_npc_context->legacy;
    }
    return af_mail_length_original(length,body);
}
