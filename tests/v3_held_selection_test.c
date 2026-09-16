#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/held_selection.c"
u32 af_test_held_selection[188];
u8 af_test_held_profile[192];

int main(void) {
    _Static_assert(sizeof(Entry)==8, "Equipment selection record stride");
    header[0]=0x41464853u;header[1]=1;header[2]=92;header[3]=8;
    Entry *rows=(Entry *)(header+4);
    for (int i=0;i<8;++i) {
        int item=0x2254+i,bit=83+i;
        rows[item-0x2200]=(Entry){item,107+i,1,32+bit/8,1u<<(bit%8),1};
    }
    for (u32 item=0;item<65536;++item) assert(af_v3_player_selected_equipment(item)==-1);
    assert(af_v3_player_selected_equipment(0xffffffffu)==-1);
    for (int kind=-1;kind<=127;++kind)
        assert(af_v3_player_passive_equipment(kind)==(kind>=2&&kind<34));
    for (int selected=0;selected<8;++selected) {
        memset(profile,0,192);Entry *r=&rows[84+selected];profile[r->profile_byte]=r->mask;
        for (int i=0;i<92;++i)
            assert(af_v3_player_selected_equipment(0x2200+i)==(i==84+selected?107+selected:-1));
        for (int kind=36;kind<=115;++kind)
            assert(af_v3_player_passive_equipment(kind)==(kind==107+selected));
    }
    Entry *r=&rows[91],saved=*r;
    for (unsigned i=0;i<sizeof(*r);++i) {
        *r=saved;((u8 *)r)[i]=0xFF;
        assert(af_v3_player_selected_equipment(0x225B)==-1);
    }
    *r=saved;r->mask=3;assert(af_v3_player_selected_equipment(0x225B)==-1);
    *r=saved;r->ready=0;assert(af_v3_player_selected_equipment(0x225B)==-1);
    *r=saved;r->passive=0;assert(af_v3_player_selected_equipment(0x225B)==114);
    assert(!af_v3_player_passive_equipment(114));
    *r=saved;
    for (int i=0;i<4;++i) {
        u32 value=header[i];header[i]^=1;
        assert(af_v3_player_selected_equipment(0x225B)==-1);
        assert(!af_v3_player_passive_equipment(114));
        assert(af_v3_player_passive_equipment(2));header[i]=value;
    }
    puts("Shared selected equipment and passive permissions pass");
}
