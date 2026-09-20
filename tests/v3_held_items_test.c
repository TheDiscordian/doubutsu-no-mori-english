#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/held_selection.c"
u32 af_test_held_selection[188];
u8 af_test_held_profile[192];
#undef header
#undef profile
#define AF_V3_POCKET_ICONS
#include "../overlays/v3/held_items.c"
u32 af_test_held_items[340];
u32 af_test_pocket_icons[512];
int af_test_held_selected(u32 item) { return af_v3_player_selected_equipment(item); }

int main(void) {
    u32 *s=af_test_held_selection;
    s[0]=0x41464853u;s[1]=1;s[2]=92;s[3]=8;
    header[0]=0x41464849u;header[1]=1;header[2]=56;header[3]=24;
    icons[0]=0x41464943u;icons[1]=1;icons[2]=56;icons[3]=8;
    Entry *selectors=(Entry *)(s+4);
    HeldItem *rows=(HeldItem *)(header+4);
    for (int i=0;i<8;++i) {
        u16 item=0x2254+i;
        selectors[item-0x2200]=(Entry){item,107+i,1,42+i/8,1u<<(i%8),1};
        rows[item-0x2224]=(HeldItem){item,600+i,0x314C+4*i,107+i,43,{0}};
        memcpy(rows[item-0x2224].name,"0123456789abcdef",16);
        icons[4+2*(item-0x2224)]=0x804A69E0u;
        icons[5+2*(item-0x2224)]=0x804A6A00u;
    }
    u8 out[20],unchanged[20];memset(unchanged,0xDB,20);
    for (u32 item=0;item<65536;++item) {
        memcpy(out,unchanged,20);
        assert(!af_v3_held_item_name(out+2,16,item));
        assert(!af_v3_held_item_price(item));assert(!memcmp(out,unchanged,20));
        assert(!af_v3_held_item_icon(item));
    }
    for (int i=0;i<8;++i) {
        memset(af_test_held_profile,0,192);af_test_held_profile[42]=1u<<i;
        for (u32 item=0x2224;item<0x225C;++item) {
            int enabled=item==0x2254u+i;memcpy(out,unchanged,20);
            assert(af_v3_held_item_name(out+2,16,item)==enabled);
            assert(af_v3_held_item_price(item)==(enabled?600u+i:0));
            assert(af_v3_held_item_price(0x10000u|item)==(enabled?600u+i:0));
            assert(af_v3_held_item_icon(item)==(enabled?icons+4+2*(item-0x2224):NULL));
            assert(!af_v3_held_item_icon(0x10000u|item));
            if (enabled) assert(!memcmp(out+2,"0123456789abcdef",16));
            else assert(!memcmp(out,unchanged,20));
            assert(out[0]==0xDB && out[1]==0xDB && out[18]==0xDB && out[19]==0xDB);
        }
        memcpy(out,unchanged,20);
        assert(!af_v3_held_item_name(out+2,15,0x2254+i));
        assert(!af_v3_held_item_name(NULL,16,0x2254+i));
        assert(!af_v3_held_item_name(out+2,16,0x12254+i));
        assert(!memcmp(out,unchanged,20));
    }
    HeldItem *last=&rows[55],saved=*last;
    for (int i=0;i<4;++i) {
        u32 prior=icons[i];icons[i]^=1;
        assert(!af_v3_held_item_icon(0x225B));icons[i]=prior;
    }
    for (int lane=0;lane<2;++lane) {
        u32 *word=icons+4+110+lane,prior=*word;
        const u32 invalid[]={0,0x804A6800u,0x804A69E1u,0x804A6FF8u,0xFFFFFFFFu};
        for (unsigned int i=0;i<sizeof(invalid)/sizeof(*invalid);++i) {
            *word=invalid[i];assert(!af_v3_held_item_icon(0x225B));
        }
        *word=prior;
    }
    for (int i=0;i<4;++i) {
        u32 prior=header[i];header[i]^=1;
        assert(!af_v3_held_item_name(out,16,0x225B));assert(!af_v3_held_item_price(0x225B));
        header[i]=prior;
    }
    last->item=0;assert(!af_v3_held_item_price(0x225B));*last=saved;
    last->kind=106;assert(!af_v3_held_item_price(0x225B));*last=saved;
    last->display|=1;assert(!af_v3_held_item_price(0x225B));*last=saved;
#ifdef AF_V3_POCKET_ICON_PALETTES
    for (u32 offset=0;offset<96;offset+=32) {
        icons[4+110]=0x804A67A0u+offset;
        assert(af_v3_held_item_icon(0x225B)==icons+4+110);
    }
    icons[4+110]=0x804A6780u;assert(!af_v3_held_item_icon(0x225B));
    icons[4+110]=0x804A67E8u;assert(!af_v3_held_item_icon(0x225B));
    icons[4+110]=0x804A67A0u;icons[5+110]=0x804A67A0u;
    assert(!af_v3_held_item_icon(0x225B));
#endif
#ifdef AF_V3_POCKET_ICON_EXTENSION
    icons[4+110]=0x804B3000u;icons[5+110]=0x804B3020u;
    assert(af_v3_held_item_icon(0x225B)==icons+4+110);
    icons[4+110]=0x804B3FC0u;icons[5+110]=0x804B3DE0u;
    assert(af_v3_held_item_icon(0x225B)==icons+4+110);
    for (unsigned lane=0;lane<2;++lane) {
        u32 old=icons[4+110+lane];
        const u32 invalid[]={0x804B2FF8u,0x804B3FF0u,0x804B4000u,0x804B3001u,0xFFFFFFFFu};
        for (unsigned i=0;i<sizeof invalid/sizeof *invalid;++i) {
            icons[4+110+lane]=invalid[i];assert(!af_v3_held_item_icon(0x225B));
        }
        icons[4+110+lane]=old;
    }
    icons[5+110]=0x804B3DF8u;assert(!af_v3_held_item_icon(0x225B));
    icons[5+110]=0x804B3020u;
    selectors[91].passive=0;
    assert(af_v3_player_selected_equipment(0x225B)==selectors[91].kind);
    assert(!af_v3_player_passive_equipment(selectors[91].kind));
#endif
    selectors[91].ready=0;assert(!af_v3_held_item_price(0x225B));
    puts("Shared held parent names, prices, selection, and bounded writes pass");
}
