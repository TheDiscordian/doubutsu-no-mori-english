#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_world.c"
const TreeRule af_v3_tree_rule={.first=0x863,.count=6,.hidden_first=0x7f,.hidden_count=3,
    .selected_item=0x223b,.stumps={0x7e,0x7d,0x7c,0x7b}};
const TreeDaily af_v3_tree_daily_config={.dead=0x869};
static int enabled,calls,ground_seen;
static u32 low_seen,high_seen,position[3];
static TreeUnit seen;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return enabled?90:-1; }
int af_v3_tree_column_native(void *column,const TreeUnit *unit,int grounded,u32 minimum,u32 maximum) {
    assert(column);++calls;seen=*unit;ground_seen=grounded;low_seen=minimum;high_seen=maximum;return 7;
}
int af_v3_tree_dig_native(const u16 *item,u32 x,u32 y,u32 z) {
    assert(item);++calls;position[0]=x;position[1]=y;position[2]=z;return 7;
}
int af_v3_tree_npc_native(u32 item) { (void)item;++calls;return 7; }
static u16 expected(u16 item) {
    switch (item) {
    case 0x864:return 0x801;case 0x865:return 0x802;case 0x866:return 0x803;
    case 0x867:case 0x868:case 0x7f:case 0x80:case 0x81:return 0x804;
    case 0x7b:return 1;case 0x7c:return 2;case 0x7d:return 3;case 0x7e:return 4;
    default:return item;
    }
}
int main(void) {
    struct {u32 before;TreeUnit unit;u32 after;} guarded;
    memset(&guarded,0xa5,sizeof(guarded));u32 column[8];memset(column,0x5a,sizeof(column));
    for (enabled=0;enabled<2;++enabled) for (u32 id=0;id<=65535;++id) {
        guarded.unit.item=(u16)id;TreeUnit original=guarded.unit;calls=0;
        u16 mapped=enabled?expected((u16)id):(u16)id;
        assert(af_v3_tree_column(column,&guarded.unit,1,0x10800,0x20804)==7);
        assert(calls==1 && seen.item==mapped && ground_seen==1);
        assert(low_seen==(mapped!=id?0xffff:0x10800) && high_seen==(mapped!=id?0:0x20804));
        seen.item=(u16)id;assert(!memcmp(&seen,&original,sizeof(seen)));
        assert(!memcmp(&guarded.unit,&original,sizeof(original)));
        int removable=enabled && (id==0x863 || id==0x869 || (id>=0x7b && id<=0x7e));
        calls=0;assert(af_v3_tree_dig(&guarded.unit.item,0x3f800000,0x80000000,0xc0000000)==(removable?1:7));
        assert(calls==!removable);
        if (!removable) assert(position[0]==0x3f800000 && position[1]==0x80000000 && position[2]==0xc0000000);
        calls=0;int walkable=enabled && id==0x863;
        assert(af_v3_tree_npc(id|0xa5a50000)==(walkable?1:7));assert(calls==!walkable);
    }
    enabled=1;
    for (u16 id=0x864;id<=0x868;++id) {
        guarded.unit.item=id;calls=0;
        assert(af_v3_tree_column(column,&guarded.unit,0,0x10863,0x20869)==0 && calls==0);
        assert(guarded.unit.item==id);
    }
    assert(guarded.before==0xa5a5a5a5 && guarded.after==0xa5a5a5a5);
    for (u32 i=0;i<8;++i) assert(column[i]==0x5a5a5a5a);
    puts("shared tree world queries pass");return 0;
}
