#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/inventory_equipment.c"
u32 af_iv_header[60],af_iv_shapes[41];
static unsigned int enabled;
static int last_resource;
static u32 resource_result=0x06000380u;
int af_iv_selected(u32 item) {
    return item>=0x2254u && item<=0x225Bu && (enabled&(1u<<(item-0x2254u))) ?
        (int)item-0x2254+107 : -1;
}
u32 af_iv_resource(int index) {last_resource=index;return resource_result;}

int main(void) {
    header[0]=0x41464956u;header[1]=1;header[2]=56;header[3]=4;
    Entry *rows=(Entry *)(header+4);
    for (int i=0;i<8;++i)rows[48+i]=(Entry){0x2254+i,26+i,107+i};
    for (u32 item=0;item<65536u;++item) {
        int expected=item==0x2200u?1:item==0x2201u?0:item==0x2202u?4:
            item==0x2203u?3:item>=0x2204u && item<0x2224u?2:5;
        assert(af_v3_inventory_kind_from_item(item)==expected);
    }
    for (int i=0;i<8;++i) {
        enabled=1u<<i;
        for (u32 item=0x2224u;item<0x225Cu;++item)
            assert(af_v3_inventory_kind_from_item(item)==(item==0x2254u+i?26+i:5));
        assert(af_v3_inventory_kind_from_item(0x12254u+i)==5);
    }
    for (int i=0;i<4;++i) {
        u32 saved=header[i];header[i]^=1;
        assert(af_v3_inventory_kind_from_item(0x225Bu)==5);header[i]=saved;
    }
    Entry saved=rows[55];
    rows[55].item=0;assert(af_v3_inventory_kind_from_item(0x225Bu)==5);rows[55]=saved;
    rows[55].preview=5;assert(af_v3_inventory_kind_from_item(0x225Bu)==5);rows[55]=saved;
    rows[55].preview=41;assert(af_v3_inventory_kind_from_item(0x225Bu)==5);rows[55]=saved;
    rows[55].world=106;assert(af_v3_inventory_kind_from_item(0x225Bu)==5);rows[55]=saved;
    alignas(16) u8 submenu_storage[0x60]={0},overlay[0x10700]={0},graph[0x400]={0};
    u8 *submenu=submenu_storage+4,*overlay_pointer=overlay,*graph_pointer=graph;
    memcpy(submenu+0x2C,&overlay_pointer,sizeof(overlay_pointer));
    u32 commands[6],*head=commands+2;
    for (int i=0;i<6;++i)commands[i]=0xDBDBDBDBu;
    memcpy(graph+0x298,&head,sizeof(head));
    shapes[26]=59;*(s16 *)(overlay+0x10016)=26;
    af_v3_inventory_static_draw(submenu,(u8 *)&graph_pointer);
    assert(last_resource==59 && commands[2]==0xDE000000u && commands[3]==resource_result);
    memcpy(&head,graph+0x298,sizeof(head));assert(head==commands+4);
    assert(commands[0]==0xDBDBDBDBu && commands[1]==0xDBDBDBDBu && commands[4]==0xDBDBDBDBu);
    for (int kind=-1;kind<=41;++kind) {
        if(kind==26)continue;
        *(s16 *)(overlay+0x10016)=kind;last_resource=-1;
        af_v3_inventory_static_draw(submenu,(u8 *)&graph_pointer);
        assert(last_resource==-1);
        u32 *observed;memcpy(&observed,graph+0x298,sizeof(observed));assert(observed==head);
    }
    *(s16 *)(overlay+0x10016)=26;resource_result=0;
    af_v3_inventory_static_draw(submenu,(u8 *)&graph_pointer);
    u32 *observed;memcpy(&observed,graph+0x298,sizeof(observed));assert(observed==head);
    puts("Shared inventory kinds, independent profiles, and static drawing bounds pass");
}
