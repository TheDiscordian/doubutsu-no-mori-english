#include <stdlib.h>
#include <string.h>
#include "../overlays/notice/reader.h"

unsigned char af_notice_posts[15][104];
unsigned int af_notice_buttons, af_notice_allocations, af_notice_releases;
unsigned int af_notice_fail_allocate, af_notice_allocation_errors;
unsigned int af_notice_original_constructs, af_notice_original_reads, af_notice_original_bodies;
unsigned int af_notice_label_count;
struct Label {
    unsigned int length;
    float x, y;
    unsigned char text[32];
} af_notice_labels[8];
static unsigned char *allocation;
static unsigned int allocated_size;

void *af_notice_test_allocate(unsigned int size) {
    ++af_notice_allocations;
    if (af_notice_fail_allocate) return NULL;
    if (allocation) { ++af_notice_allocation_errors; return NULL; }
    allocation = malloc(size+32u);
    if (!allocation) return NULL;
    allocated_size = size;
    memset(allocation, '!', size+32u);
    return allocation+7u;
}
void af_notice_test_release(void *memory) {
    unsigned int i;
    if (!allocation || memory != allocation+7u) { ++af_notice_allocation_errors; return; }
    for (i = 0; i < 7u; ++i) if (allocation[i] != '!') ++af_notice_allocation_errors;
    for (i = 7u+allocated_size; i < allocated_size+32u; ++i)
        if (allocation[i] != '!') ++af_notice_allocation_errors;
    memset(allocation, 0xDD, allocated_size+32u);
    free(allocation);
    allocation = NULL;
    ++af_notice_releases;
}
unsigned int af_notice_test_trigger(void) { return af_notice_buttons; }
unsigned char *af_notice_test_post(unsigned int index) { return af_notice_posts[index]; }
int af_notice_test_width(const unsigned char *text, unsigned int length) {
    extern int af_mail_view_widths[256];
    unsigned int i, result = 0;
    for (i = 0; i < length; ++i) result += af_mail_view_widths[text[i]];
    return (int)result;
}
void af_notice_test_label(void *game, const unsigned char *text, unsigned int length, float x, float y) {
    struct Label *value;
    (void)game;
    if (af_notice_label_count >= 8u || length > 32u) { af_notice_label_count = 1000u; return; }
    value = &af_notice_labels[af_notice_label_count++];
    value->length = length;
    value->x = x;
    value->y = y;
    memcpy(value->text, text, length);
}
void af_notice_original_construct(void *submenu) { (void)submenu; ++af_notice_original_constructs; }
void af_notice_original_read(void *submenu, void *menu, unsigned char *state) {
    (void)submenu;
    ++af_notice_original_reads;
    /* Controlled outcomes test wrapper precedence, not native input behaviour. */
    if (af_notice_buttons & 0x8000u) { state[0] = 2; state[4] = 15; }
    else if (af_notice_buttons & 0x5000u) ((unsigned int *)menu)[1] = 0;
    else if ((af_notice_buttons & 2u) && state[4]) { --state[4]; state[0] = 1; }
    else if ((af_notice_buttons & 1u) && state[4] < state[3]-1u) { ++state[4]; state[0] = 1; }
}
void af_notice_original_body(void *menu, void *game, const unsigned char *source, int length,
                               float x, float y, float *end_x, float *end_y) {
    (void)menu; (void)game; (void)source; (void)length;
    ++af_notice_original_bodies;
    *end_x = x+123.0f;
    *end_y = y+456.0f;
}
void af_notice_test_reset(void) {
    if (allocation) { free(allocation); allocation = NULL; }
    af_notice_buttons = af_notice_allocations = af_notice_releases = af_notice_fail_allocate = 0;
    af_notice_allocation_errors = af_notice_original_constructs = af_notice_original_reads = 0;
    af_notice_original_bodies = af_notice_label_count = 0;
    memset(af_notice_labels, 0, sizeof(af_notice_labels));
    memset(af_notice_posts, ' ', sizeof(af_notice_posts));
    af_notice_construct((void *)1);
}
unsigned int af_notice_cache_size(void) { return sizeof(AfNoticeCache); }
