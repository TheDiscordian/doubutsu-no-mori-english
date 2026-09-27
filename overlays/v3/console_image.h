#ifndef AF_V3_CONSOLE_IMAGE_H
#define AF_V3_CONSOLE_IMAGE_H
#include "console_save.h"
enum { AF_CONSOLE_INPUT_BYTES=1024, AF_CONSOLE_READ_FAILED=-5 };
typedef int (*AFConsoleRead)(void *context,unsigned int offset,void *destination,unsigned int bytes);
typedef struct { unsigned char data[AF_CONSOLE_INPUT_BYTES]; } __attribute__((aligned(16))) AFConsoleImageWork;
/* Read offsets are relative to the checked game pool. Every request has aligned
 * offset/destination and a positive, 16-byte-multiple length. Only one complete
 * game is decoded. Both compressed and decoded CRCs must match. Output/workspace
 * may change on failure, but metadata and saves are never written. The caller
 * must not bind the image to the emulator or persistence session until success. */
int af_v3_console_load_image(const unsigned char *metadata,unsigned int metadata_bytes,
    unsigned int game,AFConsoleRead read,void *context,unsigned int pool_bytes,
    unsigned char *image,unsigned int image_bytes,AFConsoleImageWork *workspace);
#endif
