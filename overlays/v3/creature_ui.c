/* Complete collection identities and official catch messages share one table. */
typedef unsigned char u8;
typedef unsigned int u32;
extern const u8 af_creature_ui_data[];
extern int af_v3_creature_collected(u8 *,unsigned,unsigned,unsigned);
extern int af_creature_item_type(u32);
extern u32 af_ui_native_fish_item(u32);
extern void af_ui_item_name(u32,u32),af_ui_set_message(u32);
#ifdef __mips__
#define active (*(u8 *volatile *)0x80136FD8u)
static int fish_index(const u8 *player) {
    const u8 *bobber=*(const u8 *const *)(player+0xF28);
    return bobber ? *(const int *)(bobber+0x290) : -1;
}
#else
extern u8 *af_ui_active;
extern int af_ui_fish_index(const u8 *);
#define active af_ui_active
#define fish_index af_ui_fish_index
#endif
static unsigned read16(const u8 *p) {return (unsigned)p[0]*256+p[1];}
static unsigned read32(const u8 *p) {return read16(p)*65536u+read16(p+2);}
static int table_valid(void) {
    return read32(af_creature_ui_data)==0x41464355u && read32(af_creature_ui_data+4)==1 &&
        read32(af_creature_ui_data+8)==45 && read32(af_creature_ui_data+12)==17;
}
u32 af_v3_creature_grid_item(unsigned position,unsigned page) {
    if (!table_valid() || position>=45 || (page!=0 && page!=2)) return 0;
    unsigned insect=page==2;
    unsigned index=af_creature_ui_data[(insect ? 0x40 : 0x10)+position];
    if (index>=(insect ? 40u : 41u) || !af_v3_creature_collected(active,insect,index,0)) return 0;
    if (!insect && index<32) return af_ui_native_fish_item(index);
    return (insect ? 0x2D00u : 0x2300u)+index;
}
void af_v3_creature_fish_message(u8 *player,unsigned original) {
    if (player && table_valid()) {
        int actor=fish_index(player);
        if (actor>=36 && actor<45 && af_creature_item_type(0x2320u+actor-36)==8) {
            if (read32(player+0xCF0)==0x37 && read32(player+0xD24)) {
                af_ui_item_name(0x2320u+actor-36,0);original=0x1349;
            } else original=read16(af_creature_ui_data+0x90+(actor-36)*2);
        }
    }
    af_ui_set_message(original);
}
void af_v3_creature_insect_message(u8 *player,unsigned original) {
    if (player && table_valid() && read32(player+0xE68)) {
        unsigned index=read32(player+0xF24);
        if (index>=32 && index<40 && af_creature_item_type(0x2D00+index)==18) {
            if (read32(player+0xCF0)==0x2C && read32(player+0xD14)) {
                af_ui_item_name(0x2D00+index,0);original=0xA4E;
            } else original=read16(af_creature_ui_data+0x90+(index-32+9)*2);
        }
    }
    af_ui_set_message(original);
}
