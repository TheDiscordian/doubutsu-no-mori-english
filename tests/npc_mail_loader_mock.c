#include <stdlib.h>
#include <string.h>
#include "../runtime/mail/npc_loader.h"

AfNpcMailLoaderConfig af_npc_loader_test_config;
AfNpcMailSession *af_npc_mail_session;
unsigned char af_npc_loader_blob[AF_NPC_MAIL_IMAGE_BYTES_MAX+0x1000u], af_npc_loader_log[128];
unsigned int af_npc_loader_calls, af_npc_loader_errors, af_npc_loader_fail_alloc;
unsigned int af_npc_loader_dma_failure, af_npc_loader_corrupt, af_npc_loader_mode;
unsigned int af_npc_loader_alignment, af_npc_loader_heap = 0x80200000u;
unsigned int af_npc_loader_nested_at, af_npc_loader_nested_calls;
unsigned int af_npc_loader_size, af_npc_loader_freed, af_npc_loader_input_capital;
void *af_npc_loader_override;
const unsigned char *af_npc_loader_player, *af_npc_loader_animal, *af_npc_loader_remail;
unsigned int af_npc_loader_condition, af_npc_loader_foreign;
static unsigned char *raw, *owned, *image;

static void step(unsigned int point) {
    unsigned char output[164], before[164];
    unsigned int capital;
    AfNpcMailSession *active;
    if (af_npc_loader_calls < sizeof(af_npc_loader_log)) af_npc_loader_log[af_npc_loader_calls++] = point;
    else ++af_npc_loader_errors;
    if (af_npc_loader_nested_at != point) return;
    memset(output,'!',sizeof(output));memcpy(before,output,sizeof(before));
    capital = af_mail_generation_capital;active = af_npc_mail_session;
    ++af_npc_loader_nested_calls;
    if (af_npc_mail_load(output,af_npc_loader_player,af_npc_loader_animal,af_npc_loader_remail,
                         af_npc_loader_condition,af_npc_loader_foreign)
            || memcmp(output,before,sizeof(output)) || capital != af_mail_generation_capital
            || active != af_npc_mail_session) ++af_npc_loader_errors;
}

void *af_npc_loader_test_allocate(unsigned int size) {
    step(1);af_npc_loader_size = size;
    if (af_npc_loader_fail_alloc) return 0;
    if (af_npc_loader_override) return af_npc_loader_override;
    raw = malloc(size+64u);
    if (!raw) abort();
    memset(raw,0xA5,size+64u);
    owned = raw+16u+af_npc_loader_alignment;
    memset(owned,'!',size);
    return owned;
}

void af_npc_loader_test_release(void *memory) {
    unsigned int i;
    step(7);++af_npc_loader_freed;
    if (af_npc_loader_override) {
        if (memory != af_npc_loader_override) ++af_npc_loader_errors;
        return;
    }
    if (memory != owned) { ++af_npc_loader_errors;return; }
    for (i = 0; i < 16u+af_npc_loader_alignment; ++i)
        if (raw[i] != 0xA5u) ++af_npc_loader_errors;
    for (i = 16u+af_npc_loader_alignment+af_npc_loader_size; i < af_npc_loader_size+64u; ++i)
        if (raw[i] != 0xA5u) ++af_npc_loader_errors;
    free(raw);raw = owned = image = 0;
}

unsigned int af_npc_loader_test_heap_address(void *memory) {
    if (!memory) ++af_npc_loader_errors;
    return af_npc_loader_heap;
}

int af_npc_loader_test_dma(void *destination, unsigned int source, unsigned int size) {
    step(2);image = destination;
    if (((__UINTPTR_TYPE__)image & 15u) || image < owned || image-owned > 15
            || source != af_npc_loader_test_config.vrom || size != af_npc_loader_test_config.blob_bytes)
        ++af_npc_loader_errors;
    memcpy(image,af_npc_loader_blob,size);
    if (af_npc_loader_corrupt && af_npc_loader_corrupt <= size) image[af_npc_loader_corrupt-1] ^= 1;
    return af_npc_loader_dma_failure ? -1 : 0;
}

void af_npc_loader_test_relocate(void *base, void *reloc, unsigned int link) {
    step(3);
    if (base != image || reloc != image+af_npc_loader_test_config.image_bytes
            || link != AF_NPC_MAIL_CREATOR_RAM) ++af_npc_loader_errors;
}

void af_npc_loader_test_writeback(void *base, unsigned int size) {
    step(4);
    if (base != image || size != af_npc_loader_test_config.image_bytes) ++af_npc_loader_errors;
}

void af_npc_loader_test_invalidate(void *base, unsigned int size) {
    step(5);
    if (base != image || size != af_npc_loader_test_config.image_bytes) ++af_npc_loader_errors;
}

int af_npc_loader_test_execute(void *entry, void *work, unsigned char *destination,
                               AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailSession *session = work;
    unsigned int i;
    if (entry != image+af_npc_loader_test_config.entry_offset
            || work != image+af_npc_loader_test_config.blob_bytes
            || ((__UINTPTR_TYPE__)work & 15u) || active != &af_npc_mail_session || *active
            || capital == &af_mail_generation_capital || *capital != af_mail_generation_capital
            || session->player != af_npc_loader_player || session->animal != af_npc_loader_animal
            || session->remail != af_npc_loader_remail || session->condition != af_npc_loader_condition
            || session->foreign != af_npc_loader_foreign) ++af_npc_loader_errors;
    af_npc_loader_input_capital = *capital;
    /* Touch the final work byte so sanitizer/guard checks cover the complete
     * native allocation contract, not just the host-sized session prefix.
     */
    ((unsigned char *)work)[AF_NPC_MAIL_WORK_BYTES-1] = 0x5A;
    *active = session;
    step(6);
    if (af_npc_loader_mode == 2) return 0; /* Deliberate broken scope contract. */
    *active = 0;
    if (af_npc_loader_mode == 1) { *capital = 123;return 0; }
    if (af_npc_loader_mode == 3) return 2;
    if (af_npc_loader_mode == 4) { *capital = 2;return 1; }
    for (i = 0; i < 164u; ++i) destination[i] = (unsigned char)(i*17u+*capital);
    *capital ^= 1u;
    return 1;
}
