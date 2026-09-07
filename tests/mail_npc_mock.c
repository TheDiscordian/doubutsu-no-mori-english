#include <stdlib.h>
#include <string.h>
#include "../runtime/mail/npc.h"
#include "../runtime/mail/grade.h"

unsigned int af_npc_allocations, af_npc_releases, af_npc_fail_allocate, af_npc_mock_errors;
unsigned int af_npc_sends, af_npc_native_lengths, af_npc_depth;
int af_npc_observed[3], af_npc_send_result = 42;
const unsigned char *af_npc_nested_mail;
static unsigned char *raw;
static unsigned int allocated_size;

void *af_npc_test_allocate(unsigned int size) {
    ++af_npc_allocations;
    if (af_npc_fail_allocate) return NULL;
    if (raw) ++af_npc_mock_errors;
    raw = malloc(size+32);
    if (!raw) return NULL;
    memset(raw,0xA5,size+32);
    allocated_size = size;
    return raw+7; /* Deliberately unaligned; production must align its workspace. */
}

void af_npc_test_release(void *memory) {
    unsigned int i;
    ++af_npc_releases;
    if (!raw || memory != raw+7) { ++af_npc_mock_errors; return; }
    for (i = 0; i < 7; ++i) if (raw[i] != 0xA5) ++af_npc_mock_errors;
    for (i = 7+allocated_size; i < allocated_size+32; ++i)
        if (raw[i] != 0xA5) ++af_npc_mock_errors;
    free(raw);
    raw = NULL;
}

unsigned int af_npc_test_length_original(int *length, const unsigned char *body) {
    (void)body;
    ++af_npc_native_lengths;
    *length = 123;
    return 1;
}

int af_npc_test_send_original(const unsigned char *mail) {
    AfMailNpcContext *context = af_mail_npc_context;
    ++af_npc_sends;
    if (raw) ++af_npc_mock_errors; /* Decode storage must be freed before send. */
    if (mail[0x27] == 0x80 && (!context || context->body != mail+0x34)) ++af_npc_mock_errors;
    if (!af_npc_depth && af_npc_nested_mail) {
        ++af_npc_depth;
        if (af_mail_send_npc(af_npc_nested_mail) != af_npc_send_result) ++af_npc_mock_errors;
        --af_npc_depth;
        if (af_mail_npc_context != context) ++af_npc_mock_errors;
    }
    af_npc_observed[0] = (int)af_mail_grade_native(mail+0x34);
    af_npc_observed[1] = (int)af_mail_grade_length(&af_npc_observed[2],mail+0x34);
    return af_npc_send_result;
}
