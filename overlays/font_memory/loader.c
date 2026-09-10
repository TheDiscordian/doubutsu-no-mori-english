/* Persistent font owner, separate from the title and the ordinary arenas. */
typedef unsigned int u32;
struct FontConfig { u32 vrom, blob, image, reloc, text, entry, crc, abi; };
extern u32 af_crc32(const void *, u32);

#ifdef __mips__
#define config ((volatile const struct FontConfig *)0x80194948u)
#define loaded (*(void *volatile *)0x80199F04u)
#define busy (*(volatile u32 *)0x80199F00u)
#define memsize (*(volatile const u32 *)0x80000318u)
#define owner ((unsigned char *)0x80450010u)
#define guards ((volatile u32 *)0x80450000u)
#define dma ((int (*)(void *,u32,u32))0x80026B44u)
#define relocate ((void (*)(void *,void *,u32))0x8002B9C0u)
#define writeback ((void (*)(void *,u32))0x8002FE00u)
#define invalidate ((void (*)(void *,u32))0x80034CE0u)
#define execute(image) (((int (*)(void))(image))())
#else
extern volatile struct FontConfig af_expansion_config;
extern void *af_expansion_loaded;
extern u32 af_expansion_busy, af_expansion_memsize;
extern unsigned char af_expansion_memory[0x8000];
extern int af_expansion_dma(void *,u32,u32);
extern void af_expansion_relocate(void *,void *,u32);
extern void af_expansion_writeback(void *,u32);
extern void af_expansion_invalidate(void *,u32);
extern int af_expansion_execute(void *);
#define config (&af_expansion_config)
#define loaded af_expansion_loaded
#define busy af_expansion_busy
#define memsize af_expansion_memsize
#define owner (af_expansion_memory+16)
#define guards ((u32 *)af_expansion_memory)
#define dma af_expansion_dma
#define relocate af_expansion_relocate
#define writeback af_expansion_writeback
#define invalidate af_expansion_invalidate
#define execute af_expansion_execute
#endif

int af_font_expansion_init(void) {
    struct FontConfig approved;
    unsigned char *image = owner;
    u32 i, result = 0;
    if (loaded) return 1;
    if (busy) return 0;
    for (i=0;i<8u;++i) ((u32 *)&approved)[i]=((volatile const u32 *)config)[i];
    if (approved.vrom!=0x03400000u || approved.abi!=0x41464701u
            || !approved.image || approved.image>0x7000u || (approved.image&15u)
            || approved.reloc<32u || approved.reloc>0x1000u || (approved.reloc&15u)
            || approved.blob!=approved.image+approved.reloc || approved.blob>0x7FE0u
            || approved.entry || !approved.text || approved.text>approved.image
            || (approved.text&15u)) return 0;
    /* The native title adapter supplies the existing power-off warning. Do not
       touch absent RAM or install any font hook on unsupported machines. */
    if (memsize!=0x800000u) return 1;
    busy=1;
    for (i=0;i<4u;++i) guards[i]=guards[0x1FFCu+i]=0xAF46C0DEu;
    if (dma(image,approved.vrom,approved.blob)) goto done;
    if (af_crc32(image,approved.blob)!=approved.crc) goto done;
    relocate(image,image+approved.image,0x80C00000u);
    writeback(image,approved.image);
    invalidate(image,approved.text);
    if (execute(image)!=1) goto done;
    loaded=image;
    result=1;
done:
    busy=0;
    return result;
}
