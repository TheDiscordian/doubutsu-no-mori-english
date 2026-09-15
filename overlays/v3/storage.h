#ifndef AF_V3_STORAGE_H
#define AF_V3_STORAGE_H
/* Verified virtual-ROM gap; resident RAM and saved identities are unchanged. */
#define AF_V3_STORAGE_VROM 0x02200000u
#define AF_V3_STORAGE_END 0x02400000u
#define AF_V3_CLOTHING_VROM (AF_V3_STORAGE_VROM + 0xF000u)
#ifndef AF_V3_SAVE_CODE_VROM
#define AF_V3_SAVE_CODE_VROM (AF_V3_STORAGE_VROM + 0xF400u)
#endif
#ifndef AF_V3_EXTRA_CODE_LIMIT
#define AF_V3_EXTRA_CODE_LIMIT 0xC00u
#endif
#endif
