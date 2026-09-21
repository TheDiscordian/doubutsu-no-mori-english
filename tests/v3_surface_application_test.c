#define AF_SURFACE_ROOM 1
#define main metadata_checks
#include "v3_surface_items_test.c"
#undef main
u8 **af_test_room_clip;
u32 af_test_room_scene;
u8 af_test_homes[4*0xB48];
static u32 field;
static int npc,prior_floor_calls;
int af_surface_prior_floor(void) {prior_floor_calls++;return 123;}
u32 af_surface_field(void) {return field;}
int af_surface_npc_floor(void) {return npc;}

int main(void) {
    metadata_checks();
    u32 actor_words[0x1B8/4],expected[0x1B8/4];
    u8 *actor=(u8 *)actor_words;
    SurfaceItem *rows=(SurfaceItem *)(header+4);
    for (u32 i=0;i<10;i++) rows[i].enabled=1;
    for (u32 kind=0;kind<2;kind++) for (u32 i=0;i<256;i++) {
        u32 base=0x2600+kind*256,item=base+i,pending=kind ? 0x1A8 : 0x1B0;
        u32 identity=kind ? 0x176 : 0x174;
        int valid=i<68 || (i>=73 && i<78);
        assert(af_v3_surface_allowed(item,base)==valid);
        assert(!af_v3_surface_allowed(item,base^256));
        memset(actor,0xA5,sizeof(actor_words));*(u32 *)(actor+pending)=0;
        *(short *)(actor+identity)=77;memcpy(expected,actor,sizeof(expected));
        af_test_room_clip=&actor;
        u32 (*reserve_item)(u32)=kind ? af_v3_surface_reserve_wall : af_v3_surface_reserve_floor;
        assert(reserve_item(0x12340000|item)==(valid ? base+77 : 0));
        if (valid) {
            *(u32 *)((u8 *)expected+pending)=1;
            *(u16 *)((u8 *)expected+pending+4)=(u16)item;
        }
        assert(!memcmp(actor,expected,sizeof(expected)));
        assert(!reserve_item(item)); /* Busy or invalid. */
        assert(!memcmp(actor,expected,sizeof(expected)));
        af_test_room_clip=0;assert(!reserve_item(item));
        u8 *none=0;af_test_room_clip=&none;assert(!reserve_item(item));
    }
    af_test_room_clip=&actor;
    for (u32 i=0;i<10;i++) {
        rows[i].enabled=0;
        memset(actor,0,sizeof(actor_words));memcpy(expected,actor,sizeof(expected));
        assert(!af_v3_surface_allowed(rows[i].item,rows[i].item&0xFF00));
        assert(!(i<5 ? af_v3_surface_reserve_floor(rows[i].item) : af_v3_surface_reserve_wall(rows[i].item)));
        assert(!memcmp(actor,expected,sizeof(expected)));rows[i].enabled=1;
    }
    assert(!af_v3_surface_allowed(0x2649,0x2800));
    for (u32 scene=0;scene<40;scene++) {
        af_test_room_scene=scene;
        if (scene==6 || (scene>=20 && scene<=22)) continue;
        int old=prior_floor_calls;
        assert(af_v3_surface_floor_index()==123 && prior_floor_calls==old+1);
    }
    for (u32 home=0;home<4;home++) for (u32 i=0;i<256;i++) {
        field=0x6000+home;af_test_homes[home*0xB48+0x14]=(u8)i;
        int want=(int)(i>=73 && i<78 ? i : i&63);
        af_test_room_scene=20+home%3;assert(af_v3_surface_floor_index()==want);
        af_test_room_scene=6;npc=(int)i;assert(af_v3_surface_floor_index()==want);
    }
    npc=-1;assert(af_v3_surface_floor_index()==63);
    for (u32 i=0;i<5;i++) {
        rows[i].enabled=0;npc=73+(int)i;
        assert(af_v3_surface_floor_index()==(npc&63));rows[i].enabled=1;
    }
    af_test_room_scene=20;field=0x6004;assert(af_v3_surface_floor_index()==-1);
    field=0x5FFF;assert(af_v3_surface_floor_index()==-1);
    puts("selected surface reservation, full home/NPC identity, and original-scene routing pass");
}
