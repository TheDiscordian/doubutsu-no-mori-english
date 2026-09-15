/* Explicit ordinary-town adaptation; keep the original donor role in metadata. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
#define flags ((const u8 *)0x80461E60u)
#define modes ((const u8 *)0x80461F60u)
#define metadata ((const u8 *)0x80462C00u)
#define profile ((const u8 *)0x80460020u)
#define ready (*(volatile const u32 *)0x8019ACD0u == 1u)
#define outfit ((int (*)(u32))0x80464084u)
#else
extern u8 af_v3_town_flags[20],af_v3_town_modes[20],af_v3_town_metadata[640],af_v3_town_profile[192];
extern int af_v3_town_ready,af_v3_town_outfit(u32);
#define flags af_v3_town_flags
#define modes af_v3_town_modes
#define metadata af_v3_town_metadata
#define profile af_v3_town_profile
#define ready af_v3_town_ready
#define outfit af_v3_town_outfit
#endif

int af_v3_town_eligible(int index) {
    if (index>=0 && index<216) return 1;
    if (!ready || index<218 || index>=238) return 0;
    u32 slot=(u32)index-218u;
    const u8 *row=metadata+slot*32u;
    if (flags[slot]!=1 || modes[slot]!=1 || !(profile[index/8]&(1u<<(index&7)))
            || row[0]!=0xE0 || row[1]!=index || row[4]>=6 || row[7]!=1
            || (row[6]!=0 && row[6]!=2)) return 0;
    return outfit(((u32)row[30]<<8)|row[31]);
}
