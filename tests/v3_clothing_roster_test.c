#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/clothing_roster.c"
#undef records
#define AF_V3_OUTFIT_READY af_v3_roster_outfit_ready
#define main unused_pilot_fixture
#include "v3_villager_text_test.c"
#undef main

struct Clothing af_v3_roster_clothing[3];
u8 af_v3_roster_profile[192];

int main(void) {
    u8 raw[96], villagers[640], expected[sizeof(animal)], item[4];
    assert(fread(raw,1,sizeof(raw),stdin)==sizeof(raw));
    assert(fread(villagers,1,sizeof(villagers),stdin)==sizeof(villagers));
    assert(fread(af_v3_roster_profile,1,192,stdin)==192 && getchar()==EOF);
    for (u32 i=0;i<3;++i) {
        const u8 *p=raw+i*32;
        struct Clothing *row=af_v3_roster_clothing+i;
        memcpy(row,p,32);
        row->item=((u32)p[0]<<8)|p[1]; row->index=((u32)p[2]<<8)|p[3];
        row->vrom=((u32)p[4]<<24)|((u32)p[5]<<16)|((u32)p[6]<<8)|p[7];
        row->price=((u32)p[8]<<8)|p[9];
        assert(!row->padding);
    }
    for (u32 i=0;i<3;++i) {
        struct Clothing *row=af_v3_roster_clothing+i, valid=*row;
        assert(af_v3_roster_clothing_record(row->item)==row);
        assert(af_v3_roster_clothing_source(row->index,0)==row->vrom);
        assert(af_v3_roster_clothing_source(row->index,1)==row->vrom+512);
        item[0]=row->item>>8; item[1]=row->item; item[2]=0xA5; item[3]=0x5A;
        assert(af_v3_roster_clothing_index(item)==row->index && item[2]==0xA5 && item[3]==0x5A);
        assert(af_v3_roster_outfit_ready(row->item));
        for (u32 damage=0;damage<7;++damage) {
            *row=valid;
            if (damage==0) row->enabled=0;
            if (damage==1) row->item^=1;
            if (damage==2) row->index^=1;
            if (damage==3) row->vrom++;
            if (damage==4) row->reserved=1;
            if (damage==5) row->padding=1;
            if (damage==6) af_v3_roster_profile[160+((valid.item&255)>>3)]^=1u<<(valid.item&7);
            assert(!af_v3_roster_clothing_record(valid.item));
            assert(!af_v3_roster_clothing_source(valid.index,0));
            assert(!af_v3_roster_outfit_ready(valid.item));
            if (damage==6) af_v3_roster_profile[160+((valid.item&255)>>3)]^=1u<<(valid.item&7);
        }
        *row=valid;
    }
    for (int i=0;i<256;++i) {
        assert(af_v3_roster_clothing_source(i,0)==0xB68000u+(u32)i*512u);
        assert(af_v3_roster_clothing_source(i,1)==0xB88000u+(u32)i*32u);
        assert(af_v3_roster_outfit_ready(0x2400u+(u32)i));
    }
    const int invalid[]={-1,256,0x1000,0x1019,0x101C,0x10BE,0x10C0,0x1100,0x7FFFFFFF};
    for (u32 i=0;i<sizeof(invalid)/sizeof(*invalid);++i)
        assert(!af_v3_roster_clothing_source(invalid[i],0));
    assert(!af_v3_roster_clothing_source(0x101A,2));
    assert(!af_v3_roster_clothing_record(0x1341Au));
    assert(!af_v3_roster_clothing_index(0));
    memcpy(af_v3_land_info,"Forest!!\x12\x34",10);
    for (u32 i=0;i<20;++i) {
        const u8 *p=villagers+32*i;
        struct Villager *row=af_v3_villagers+i;
        memcpy(row,p,32);
        row->actor=((u32)p[0]<<8)|p[1]; row->cloth=((u32)p[2]<<8)|p[3];
        row->native_cloth=((u32)p[30]<<8)|p[31];
        assert(row->native_cloth && af_v3_roster_outfit_ready(row->native_cloth));
        memset(expected,0xA5,sizeof(expected));
        expected[0]=row->actor>>8; expected[1]=row->actor; expected[11]=row->personality;
        memcpy(expected+2,"\x12\x34" "Forest",8); memcpy(expected+0x4E5,row->key,4);
        expected[0x520]=row->native_cloth>>8; expected[0x521]=row->native_cloth;
        memset(animal,0xA5,sizeof(animal));
        af_v3_set_index(animal,row->actor&255);
        assert(!memcmp(animal,expected,sizeof(animal)));
    }
    af_v3_roster_profile[163]&=~4u;
    memset(animal,0xA5,sizeof(animal)); memcpy(expected,animal,sizeof(expected));
    af_v3_set_index(animal,218);
    assert(!memcmp(animal,expected,sizeof(animal)));
    assert(af_v3_roster_outfit_ready(0x341B) && af_v3_roster_outfit_ready(0x34BF));
    puts("Three garments, complete twenty-villager defaults, subset and corruption guards pass");
    return 0;
}
