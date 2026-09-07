#include <string.h>
#include <stdlib.h>
#include "../runtime/mail/reader.h"

unsigned int af_mail_reader_buttons, af_mail_reader_copies;
unsigned int af_reader_allocations, af_reader_releases, af_reader_fail_allocate;
unsigned int af_reader_allocation_size, af_reader_live_allocations, af_reader_allocation_errors;
static unsigned char *allocated;
static unsigned int allocated_size;
void *af_mail_reader_test_allocate(unsigned int size) {
    ++af_reader_allocations;
    af_reader_allocation_size = size;
    if (af_reader_fail_allocate)
        return NULL;
    if (allocated) {
        ++af_reader_allocation_errors;
        return NULL;
    }
    allocated = malloc(size+32u);
    if (!allocated)
        return NULL;
    memset(allocated,'!',size+32u);
    allocated_size = size;
    ++af_reader_live_allocations;
    /* Exercise rounding even on hosts whose malloc already aligns to sixteen. */
    return allocated+7;
}
void af_mail_reader_test_release(void *memory) {
    unsigned int i;
    if (!allocated || memory != allocated+7) {
        ++af_reader_allocation_errors;
        return;
    }
    for (i = 0; i < 7u; ++i)
        if (allocated[i] != '!') ++af_reader_allocation_errors;
    for (i = 7u+allocated_size; i < allocated_size+32u; ++i)
        if (allocated[i] != '!') ++af_reader_allocation_errors;
    /* Poison released scratch so later drawing cannot accidentally depend on it. */
    memset(allocated,0xDD,allocated_size+32u);
    free(allocated);
    allocated = NULL;
    --af_reader_live_allocations;
    ++af_reader_releases;
}
void af_mail_reader_test_copy(unsigned char *destination, const unsigned char *source) {
    ++af_mail_reader_copies;
    memcpy(destination, source, 164);
}
unsigned int af_mail_reader_test_trigger(void) { return af_mail_reader_buttons; }
void af_mail_reader_test_reset(void) {
    if (allocated) {
        free(allocated);
        allocated = NULL;
    }
    af_reader_allocations = af_reader_releases = af_reader_fail_allocate = 0;
    af_reader_allocation_size = af_reader_live_allocations = af_reader_allocation_errors = 0;
    memset(&af_mail_reader, 0, sizeof(af_mail_reader));
}
