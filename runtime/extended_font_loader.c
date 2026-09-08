/* One system-heap owner survives every gameplay-arena teardown. */
typedef unsigned int u32;

struct FontConfig { u32 vrom, blob, image, reloc, text, entry, crc, abi; };
void *af_extended_font_image;
static u32 busy;

#ifdef __mips__
#define config ((volatile const struct FontConfig *)0x80194948u)
#define allocate ((void *(*)(u32))0x8002BC60u)
#define release ((void (*)(void *))0x8002BC90u)
#define dma ((int (*)(void *,u32,u32))0x80026B44u)
#define relocate ((void (*)(void *,void *,u32))0x8002B9C0u)
#define writeback ((void (*)(void *,u32))0x8002FE00u)
#define invalidate ((void (*)(void *,u32))0x80034CE0u)
#define address(memory) ((u32)(memory))
#define execute(image) (((int (*)(void))(image))())
#else
extern volatile struct FontConfig af_font_test_config;
extern void *af_font_test_allocate(u32);
extern void af_font_test_release(void *);
extern int af_font_test_dma(void *,u32,u32);
extern void af_font_test_relocate(void *,void *,u32);
extern void af_font_test_writeback(void *,u32);
extern void af_font_test_invalidate(void *,u32);
extern u32 af_font_test_address(void *);
extern int af_font_test_execute(void *);
#define config (&af_font_test_config)
#define allocate af_font_test_allocate
#define release af_font_test_release
#define dma af_font_test_dma
#define relocate af_font_test_relocate
#define writeback af_font_test_writeback
#define invalidate af_font_test_invalidate
#define address af_font_test_address
#define execute af_font_test_execute
#endif

int af_extended_font_init(void) {
    struct FontConfig approved;
    unsigned char *image;
    void *allocation;
    u32 i, bit, crc, size, pointer;
    if (af_extended_font_image) return 1;
    if (busy) return 0;
    for (i=0;i<8u;++i) ((u32 *)&approved)[i]=((volatile const u32 *)config)[i];
    if (!approved.vrom) {
        for (i=1;i<8u;++i) if (((u32 *)&approved)[i]) return 0;
        return 1;
    }
    if (approved.vrom!=0x03400000u || approved.abi!=0x41464701u
            || !approved.image || approved.image>0x3000u || (approved.image&15u)
            || approved.reloc<32u || approved.reloc>0x1000u || (approved.reloc&15u)
            || approved.blob!=approved.image+approved.reloc || approved.entry
            || !approved.text || approved.text>approved.image || (approved.text&15u)) return 0;
    busy=1;
    size=approved.blob+15u;
    allocation=allocate(size);
    if (!allocation) { busy=0;return 0; }
    pointer=address(allocation);
    if (pointer<0x8019C8E0u || pointer>0x80400000u || size>0x80400000u-pointer) goto failed;
    image=(unsigned char *)(((__UINTPTR_TYPE__)allocation+15u)&~(__UINTPTR_TYPE__)15u);
    if (dma(image,approved.vrom,approved.blob)) goto failed;
    crc=0xFFFFFFFFu;
    for (i=0;i<approved.blob;++i) {
        crc^=image[i];
        for (bit=0;bit<8u;++bit) crc=(crc>>1)^((0u-(crc&1u))&0xEDB88320u);
    }
    if ((crc^0xFFFFFFFFu)!=approved.crc) goto failed;
    relocate(image,image+approved.image,0x80C00000u);
    writeback(image,approved.image);
    invalidate(image,approved.text);
    if (execute(image)!=1) goto failed;
    af_extended_font_image=image;
    busy=0;
    return 1; /* Intentionally retained in the system arena until machine reset. */
failed:
    release(allocation);
    busy=0;
    return 0;
}
