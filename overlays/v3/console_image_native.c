#include "console_image.h"
typedef unsigned char u8;
typedef unsigned int u32;
extern int af_console_pi_read(u32,void *,u32);
#ifdef __mips__
#define metadata ((const u8 *)AF_CONSOLE_METADATA_RAM)
#else
extern const u8 *af_test_console_metadata;
#define metadata af_test_console_metadata
#endif

/* The workspace belongs to the caller, not the save encoder or game image.
 * Metadata/code are authenticated by startup; every image is authenticated by
 * the bounded decoder before its caller may bind it to the emulator. */
static int read_pool(void *context,u32 offset,void *destination,u32 bytes) {
    (void)context;
    if(!destination || ((__UINTPTR_TYPE__)destination&15) || (offset&15) ||
        !bytes || (bytes&15) || bytes>AF_CONSOLE_INPUT_BYTES ||
        offset>AF_CONSOLE_POOL_BYTES || bytes>AF_CONSOLE_POOL_BYTES-offset)
        return AF_CONSOLE_BAD_ARGUMENT;
    return af_console_pi_read(AF_CONSOLE_POOL_ROM+offset,destination,bytes);
}
int af_v3_console_image_native_load(u32 game,void *image,u32 bytes,AFConsoleImageWork *workspace) {
    return af_v3_console_load_image(metadata,AF_CONSOLE_METADATA_BYTES,game,
        read_pool,0,AF_CONSOLE_POOL_BYTES,image,bytes,workspace);
}
