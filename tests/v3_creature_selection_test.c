/* Actual cartridge table + profile -> readers -> catches -> saved collections. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/creature_items.c"
#include "../overlays/v3/save_runtime.h"

u32 af_test_creature_items[128];
struct AfSaveRuntime af_creature_collection_state;
u8 af_creature_players[4*0xBD0],*af_creature_active;
static u8 current[192],enabled[17];
static unsigned read16(const u8 *p) {return p[0]*256u+p[1];}
static unsigned read32(const u8 *p) {return read16(p)*65536u+read16(p+2);}
unsigned af_v3_creature_profile_byte(unsigned);
void af_v3_creature_notice_fish(u8 *,int);
int af_v3_creature_collected(u8 *,unsigned,unsigned,unsigned);
int af_creature_profile(u32 index) {
    const Creature *rows=(const Creature *)(af_test_creature_items+4);
    for (unsigned i=0;i<17;i++) if (index==1024+((rows[i].display&4095u)>>2))
        return enabled[i] && (current[32+(index-1024)/8]&(1u<<((index-1024)&7)));
    return 0;
}
int af_creature_prior_name(u8 *p,u32 n,u32 item) {(void)p;(void)n;return (int)item;}
int af_creature_prior_type(u32 item) {return (int)item;}
u32 af_creature_prior_price(u32 item) {return item;}
u16 af_creature_prior_display(u32 item) {return (u16)item;}
u16 af_creature_prior_pocket(u32 item) {return (u16)item;}
void af_v3_save_halt(int error) {(void)error;abort();}
void af_v3_require_save_state(void) {
    for (unsigned i=0;i<4;i++) assert(af_creature_collection_state.working[AF_SAVE_CREATURE_OFFSET+i]==af_v3_creature_profile_byte(i));
}
u32 af_v3_surface_profile_byte(u32 i) {(void)i;return 0;}

int main(int argc,char **argv) {
    assert(argc==2);FILE *input=fopen(argv[1],"rb");assert(input);
    u8 raw[492],records[17*80];
    assert(fread(raw,1,sizeof(raw),input)==sizeof(raw));
    assert(fread(current,1,sizeof(current),input)==sizeof(current));
    assert(fread(records,1,sizeof(records),input)==sizeof(records));
    assert(fgetc(input)==EOF);fclose(input);
    for (unsigned i=0;i<4;i++) af_test_creature_items[i]=read32(raw+i*4);
    Creature *rows=(Creature *)(af_test_creature_items+4);unsigned total=0;
    for (unsigned i=0;i<17;i++) {
        const u8 *p=raw+16+i*28;Creature *r=rows+i;
        r->item=(u16)read16(p);r->display=(u16)read16(p+2);r->price=(u16)read16(p+4);
        r->type=p[6];r->source=p[7];r->ready=read32(p+8);memcpy(r->name,p+12,16);
        assert(read16(records+i*80+2)==r->display);enabled[i]=(u8)read32(records+i*80+4);
        assert(r->ready==enabled[i] && (r->ready==0 || i<9));total+=enabled[i];
        if (enabled[i]) {
            u8 name[16];assert(af_v3_creature_item_type(r->item)==8);
            assert(af_v3_creature_item_name(name,16,r->item));assert(!memcmp(name,r->name,16));
            assert(af_v3_creature_item_price(r->item)==r->price);
            assert(af_v3_creature_room_display(r->item)==r->display);
            for (unsigned rot=0;rot<4;rot++) assert(af_v3_creature_room_pocket(r->display+rot)==r->item);
        } else assert(!af_v3_creature_item_type(r->item) && !af_v3_creature_room_display(r->item));
    }
    assert(total>0);u8 *state=af_creature_collection_state.working;
    memcpy(state,current,sizeof(current));
    for (unsigned i=0;i<4;i++) state[AF_SAVE_CREATURE_OFFSET+i]=(u8)af_v3_creature_profile_byte(i);
    u8 player[0x13E0]={0};
    for (unsigned person=0;person<4;person++) {
        af_creature_active=af_creature_players+person*0xBD0;
        for (unsigned i=0;i<9;i++) {
            af_v3_creature_notice_fish(player,(int)i+36);
            assert(af_v3_creature_collected(af_creature_active,0,32+i,0)==!!enabled[i]);
        }
    }
    static u8 bank[AF_SAVE_BANK],restored[AF_SAVE_STATE],unchanged[AF_SAVE_BANK];
    bank[8]=bank[0x2F68]=0x30;bank[9]=bank[0x2F69]=1;
    assert(af_v3_save_pack(bank,sizeof(bank),state)==AF_SAVE_OK);
    assert(af_v3_save_check(bank,sizeof(bank),current,restored)==AF_SAVE_OK);
    assert(!memcmp(state,restored,sizeof(restored)));memcpy(unchanged,bank,sizeof(bank));
    for (unsigned i=0;i<9;i++) if (enabled[i]) {
        rows[i].ready=0;memset(restored,0xC7,sizeof(restored));
        assert(af_v3_save_check(bank,sizeof(bank),current,restored)==AF_SAVE_PROFILE_MISSING);
        for (unsigned j=0;j<sizeof(restored);j++) assert(restored[j]==0xC7);
        assert(!memcmp(bank,unchanged,sizeof(bank)));rows[i].ready=1;
        enabled[i]=0;assert(!af_v3_creature_item_type(rows[i].item));
        assert(af_v3_save_check(bank,sizeof(bank),current,0)==AF_SAVE_PROFILE_MISSING);enabled[i]=1;
    }
    puts("Selected parent/display identities, four-player catches, and save-profile rejection pass");
    return 0;
}
