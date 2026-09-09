/* Runs once from the native free-setter span, then its entry becomes the setter. */
typedef unsigned int u32;
extern void *af_allocate(u32);
extern void af_release(void *);
extern int af_dma(void *, u32, u32);
extern u32 af_crc32(const void *, u32);
extern void af_relocate(void *, void *, u32);
extern void af_writeback(void *, u32);
extern void af_invalidate(void *, u32);

int af_text_extension_boot(void) {
    void *allocation = af_allocate(AF_BLOB_SIZE+15u);
    unsigned char *image;
    u32 address = (u32)allocation;
    if (!allocation) return 0;
    if (address < 0x8019C8E0u || address > 0x80400000u-(AF_BLOB_SIZE+15u)) goto failed;
    image = (unsigned char *)((address+15u) & ~15u);
    if (af_dma(image, 0x03A00000u, AF_BLOB_SIZE)) goto failed;
    if (af_crc32(image, AF_BLOB_SIZE) != AF_BLOB_CRC) goto failed;
    af_relocate(image, image+AF_IMAGE_SIZE, 0x80D00000u);
    af_writeback(image, AF_IMAGE_SIZE);
    af_invalidate(image, AF_IMAGE_SIZE);
    if (((int (*)(void))image)() != 1) goto failed;
    return 1; /* This system-arena allocation persists until machine reset. */
failed:
    af_release(allocation);
    return 0;
}
