/* Checked additive garments shared by item, NPC, player, and default readers. */
#include "clothing.h"
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
#define records ((const struct Clothing *)0x80462820u)
#define profile ((const u8 *)0x80460020u)
#else
extern struct Clothing af_v3_roster_clothing[3];
extern u8 af_v3_roster_profile[192];
#define records af_v3_roster_clothing
#define profile af_v3_roster_profile
#endif

const struct Clothing *af_v3_roster_clothing_record(u32 item) {
    u32 slot, source;
    if (item==0x34BFu) { slot=0; source=0x0220F000u; }
    else if (item==0x341Au) { slot=1; source=0x022E2000u; }
    else if (item==0x341Bu) { slot=2; source=0x022E2400u; }
    else return 0;
    const struct Clothing *row=records+slot;
    u32 bit=item&255u;
    if (row->item!=item || row->index!=item-0x2400u || row->vrom!=source ||
            row->enabled!=1 || row->reserved || row->padding ||
            !(profile[160+(bit>>3)] & (1u<<(bit&7u)))) return 0;
    return row;
}

u32 af_v3_roster_clothing_source(int index, u32 palette) {
    if (palette>1) return 0;
    if (index>=0 && index<256)
        return palette ? 0x00B88000u+(u32)index*32u : 0x00B68000u+(u32)index*512u;
    if (index<0x1000 || index>0x10FF) return 0;
    const struct Clothing *row=af_v3_roster_clothing_record(0x2400u+(u32)index);
    return row ? row->vrom+(palette ? 512u : 0u) : 0;
}

int af_v3_roster_clothing_index(u8 *item) {
    if (!item) return 0;
    u32 value=((u32)item[0]<<8)|item[1];
    if (value>=0x2400u && value<0x2500u) return value-0x2400u;
    const struct Clothing *row=af_v3_roster_clothing_record(value);
    if (row) return row->index;
    item[0]=0x24; item[1]=0;
    return 0;
}

int af_v3_roster_outfit_ready(u32 cloth) {
    if (cloth>=0x2400u && cloth<0x2500u) return 1;
    return af_v3_roster_clothing_record(cloth)!=0;
}
