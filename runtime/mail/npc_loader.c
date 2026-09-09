#include "npc_loader.h"
#include "../crc32.h"

unsigned int af_mail_generation_capital;
static unsigned int busy;

#ifdef __mips__
typedef char loader_prefix_check[sizeof(AfNpcMailSession) == 32 ? 1 : -1];
#define config ((volatile const AfNpcMailLoaderConfig *)0x80194928u)
#define allocate ((void *(*)(unsigned int))0x8009BFC0u)
#define release ((void (*)(void *))0x8009C040u)
#define dma ((int (*)(void *, unsigned int, unsigned int))0x80026B44u)
#define relocate ((void (*)(void *, void *, unsigned int))0x8002B9C0u)
#define writeback ((void (*)(void *, unsigned int))0x8002FE00u)
#define invalidate ((void (*)(void *, unsigned int))0x80034CE0u)
#define heap_address(memory) ((unsigned int)(memory))
static int execute(void *entry, void *work, unsigned char *destination,
                   AfNpcMailSession **active, unsigned int *capital) {
    return ((int (*)(void *, unsigned char *, AfNpcMailSession **, unsigned int *))entry)
        (work,destination,active,capital);
}
#else
extern AfNpcMailLoaderConfig af_npc_loader_test_config;
extern void *af_npc_loader_test_allocate(unsigned int);
extern void af_npc_loader_test_release(void *);
extern int af_npc_loader_test_dma(void *, unsigned int, unsigned int);
extern void af_npc_loader_test_relocate(void *, void *, unsigned int);
extern void af_npc_loader_test_writeback(void *, unsigned int);
extern void af_npc_loader_test_invalidate(void *, unsigned int);
extern unsigned int af_npc_loader_test_heap_address(void *);
extern int af_npc_loader_test_execute(void *, void *, unsigned char *, AfNpcMailSession **, unsigned int *);
#define config (&af_npc_loader_test_config)
#define allocate af_npc_loader_test_allocate
#define release af_npc_loader_test_release
#define dma af_npc_loader_test_dma
#define relocate af_npc_loader_test_relocate
#define writeback af_npc_loader_test_writeback
#define invalidate af_npc_loader_test_invalidate
#define heap_address af_npc_loader_test_heap_address
#define execute af_npc_loader_test_execute
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    return a && b && (x <= y ? y-x < as : x-y < bs);
}

unsigned char *af_npc_mail_load(unsigned char *destination, const unsigned char *player,
                               const unsigned char *animal, const unsigned char *remail,
                               unsigned int condition, unsigned int foreign) {
    AfNpcMailLoaderConfig approved;
    unsigned int size, capital, result = 0;
    void *allocation;
    unsigned char *image;
    AfNpcMailSession *work;
    if (!destination || !player || (!animal && !remail) || busy || af_npc_mail_session
            || af_mail_generation_capital > 1u || condition > 1u || foreign > 1u
            || foreign != (remail != 0)
            || (((__UINTPTR_TYPE__)player | (__UINTPTR_TYPE__)animal | (__UINTPTR_TYPE__)remail) & 1u)
            || overlap(destination,164,&af_mail_generation_capital,sizeof(af_mail_generation_capital))
            || overlap(destination,164,&af_npc_mail_session,sizeof(af_npc_mail_session))
            || overlap(destination,164,&busy,sizeof(busy))) return 0;
    for (size = 0; size < sizeof(approved); ++size)
        ((unsigned char *)&approved)[size] = ((volatile const unsigned char *)config)[size];
    if (approved.vrom != AF_NPC_MAIL_CREATOR_VROM || approved.abi != AF_NPC_MAIL_LOADER_ABI
            || !approved.image_bytes || approved.image_bytes > AF_NPC_MAIL_IMAGE_BYTES_MAX || (approved.image_bytes & 15u)
            || approved.relocation_bytes < 32u || approved.relocation_bytes > 0x1000u
            || (approved.relocation_bytes & 15u)
            || approved.blob_bytes != approved.image_bytes+approved.relocation_bytes
            || !approved.text_bytes || approved.text_bytes > approved.image_bytes || (approved.text_bytes & 15u)
            || (approved.entry_offset & 3u) || approved.entry_offset >= approved.text_bytes) return 0;
    busy = 1;
    size = approved.blob_bytes+AF_NPC_MAIL_WORK_BYTES+15u;
    allocation = allocate(size);
    if (!allocation) { busy = 0; return 0; }
    if (!af_npc_mail_heap_range(heap_address(allocation),size)
            || overlap(allocation,size,destination,164) || overlap(allocation,size,player,16)
            || overlap(allocation,size,animal,12) || overlap(allocation,size,remail,18)) goto done;
    image = (unsigned char *)(((__UINTPTR_TYPE__)allocation+15u)&~(__UINTPTR_TYPE__)15u);
    if (dma(image,approved.vrom,approved.blob_bytes) != 0
            || af_crc32(image,approved.blob_bytes) != approved.crc32) goto done;
    /* The module-approved CRC binds the complete build-validated relocation
     * inventory and code. Nothing from this allocation executes before it.
     */
    relocate(image,image+approved.image_bytes,AF_NPC_MAIL_CREATOR_RAM);
    writeback(image,approved.image_bytes);
    invalidate(image,approved.image_bytes);
    work = (AfNpcMailSession *)(image+approved.blob_bytes);
    work->player = player;
    work->animal = animal;
    work->remail = remail;
    work->condition = condition;
    work->foreign = foreign;
    capital = af_mail_generation_capital;
    result = execute(image+approved.entry_offset,work,destination,&af_npc_mail_session,&capital) == 1;
    if (af_npc_mail_session || capital > 1u) result = 0;
    af_npc_mail_session = 0;
    if (result) af_mail_generation_capital = capital;
done:
    release(allocation);
    busy = 0;
    return result ? destination : 0;
}
