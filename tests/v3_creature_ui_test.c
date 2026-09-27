/* Check every UI identity and catch-message branch against the installed table. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ui_data.h"
typedef unsigned char u8;
typedef unsigned int u32;
u32 af_v3_creature_grid_item(unsigned,unsigned);
void af_v3_creature_fish_message(u8 *,unsigned),af_v3_creature_insect_message(u8 *,unsigned);
static u8 player[0x13E0],resident[0xBD0];
u8 *af_ui_active=resident;
static unsigned mask,seen[2][41],message,name,name_calls,message_calls;
static int actor;
static void word(u8 *p,unsigned n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
int af_ui_fish_index(const u8 *p) {assert(p==player);return actor;}
int af_creature_item_type(u32 id) {
    unsigned i=id<0x2D00 ? id-0x2320 : id-0x2D20+9;
    return i<17 && (mask&(1u<<i)) ? (i<9 ? 8 : 18) : 0;
}
int af_v3_creature_collected(u8 *p,unsigned kind,unsigned i,unsigned mark) {
    assert(!mark && kind<2 && i<(kind ? 40u : 41u));
    return p==resident && seen[kind][i] && (i<32 || af_creature_item_type((kind ? 0x2D00 : 0x2300)+i));
}
u32 af_ui_native_fish_item(u32 i) {assert(i<32);return 0x2300+i;}
void af_ui_item_name(u32 id,u32 field) {assert(!field);name=id;name_calls++;}
void af_ui_set_message(u32 id) {message=id;message_calls++;}
static unsigned target(unsigned i) {
    return af_creature_ui_data[0x90+2*i]*256u+af_creature_ui_data[0x91+2*i];
}
static void reset_message(void) {message=0;name=0;name_calls=0;message_calls=0;}
int main(void) {
    mask=0x1FFFF;
    for (unsigned kind=0;kind<2;kind++) {
        unsigned count=kind ? 40 : 41,hits[41]={0};
        for (unsigned i=0;i<count;i++) seen[kind][i]=1;
        for (unsigned pos=0;pos<45;pos++) {
            unsigned i=af_creature_ui_data[(kind ? 0x40 : 0x10)+pos];
            u32 item=af_v3_creature_grid_item(pos,kind ? 2 : 0);
            if (i>=count) assert(!item);
            else {
                assert(item==(kind ? 0x2D00u : 0x2300u)+i);hits[i]++;
                seen[kind][i]=0;assert(!af_v3_creature_grid_item(pos,kind ? 2 : 0));seen[kind][i]=1;
                if (i>=32) {
                    unsigned bit=i-32+(kind ? 9 : 0);mask^=1u<<bit;
                    assert(!af_v3_creature_grid_item(pos,kind ? 2 : 0));mask^=1u<<bit;
                }
            }
        }
        for (unsigned i=0;i<count;i++) assert(hits[i]==1);
    }
    assert(!af_v3_creature_grid_item(45,0) && !af_v3_creature_grid_item(~0u,2));
    assert(!af_v3_creature_grid_item(0,1) && !af_v3_creature_grid_item(0,3));
    af_ui_active=0;assert(!af_v3_creature_grid_item(0,0));af_ui_active=resident;
    for (unsigned i=0;i<9;i++) {
        actor=36+(int)i;
        for (unsigned final=0;final<2;final++) {
            memset(player,0,sizeof(player));word(player+0xCF0,0x37);word(player+0xD24,final);
            reset_message();af_v3_creature_fish_message(player,0x7000);
            assert(message_calls==1 && message==(final ? 0x1349 : target(i)));
            assert(name_calls==final && (!final || name==0x2320+i));
        }
        word(player+0xCF0,0);reset_message();af_v3_creature_fish_message(player,0x7000);
        assert(message==target(i) && !name_calls); /* Stale completion flag is ignored. */
        mask^=1u<<i;reset_message();af_v3_creature_fish_message(player,0x7000);
        assert(message==0x7000 && !name_calls);mask^=1u<<i;
    }
    for (actor=-1;actor<=46;actor++) if (actor<36 || actor>=45) {
        reset_message();af_v3_creature_fish_message(player,0x7000);
        assert(message==0x7000 && message_calls==1 && !name_calls);
    }
    for (unsigned i=0;i<8;i++) {
        for (unsigned final=0;final<2;final++) {
            memset(player,0,sizeof(player));word(player+0xE68,1);word(player+0xF24,32+i);
            word(player+0xCF0,0x2C);word(player+0xD14,final);
            reset_message();af_v3_creature_insect_message(player,0x7000);
            assert(message_calls==1 && message==(final ? 0xA4E : target(9+i)));
            assert(name_calls==final && (!final || name==0x2D20+i));
        }
        word(player+0xCF0,0);reset_message();af_v3_creature_insect_message(player,0x7000);
        assert(message==target(9+i) && !name_calls);
        mask^=1u<<(i+9);reset_message();af_v3_creature_insect_message(player,0x7000);
        assert(message==0x7000 && !name_calls);mask^=1u<<(i+9);
        word(player+0xE68,0);reset_message();af_v3_creature_insect_message(player,0x7000);
        assert(message==0x7000 && !name_calls);
    }
    word(player+0xE68,1);
    for (unsigned i=0;i<=41;i++) if (i<32 || i>=40) {
        word(player+0xF24,i);reset_message();af_v3_creature_insect_message(player,0x7000);
        assert(message==0x7000 && message_calls==1 && !name_calls);
    }
    reset_message();af_v3_creature_fish_message(0,123);assert(message==123);
    reset_message();af_v3_creature_insect_message(0,124);assert(message==124);
    puts("All 81 collection identities and 17 catch-message routes pass");
    return 0;
}
