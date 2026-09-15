/* My_Room owns these banks until its native teardown; never pass them to free. */
#ifndef AF_V3_FURNITURE_BANKS_H
#define AF_V3_FURNITURE_BANKS_H
#define AF_V3_BANK_POOL_START 0x80500000u
#define AF_V3_BANK_POOL_DATA (AF_V3_BANK_POOL_START + 16u)
#define AF_V3_BANK_BYTES 0x2400u
#define AF_V3_BANK_COUNT 100u
#define AF_V3_BANK_POOL_GUARD (AF_V3_BANK_POOL_DATA + AF_V3_BANK_COUNT * AF_V3_BANK_BYTES)
#define AF_V3_BANK_POOL_END (AF_V3_BANK_POOL_GUARD + 16u)
#define AF_V3_BANK_GUARD 0xAF42C0DEu
_Static_assert(AF_V3_BANK_POOL_START >= 0x80482000u, "Furniture overlaps resident imports");
_Static_assert(AF_V3_BANK_POOL_END <= 0x807DA800u, "Furniture overlaps fault framebuffer");
#endif
