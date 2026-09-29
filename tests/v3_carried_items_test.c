#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/carried_items.c"
#include "../overlays/v3/carried_menu.c"

u32 af_test_carried_header[8+8*AF_CARRY_COUNT];
static u32 calls,event_mask;
static u32 board_words[48],overlay_token,submenu_token,load_calls;
void *af_test_carried_menu_pointer(void *p,u32 at) {
    if(p==&submenu_token && at==0x2C)return &overlay_token;
    if(p==&overlay_token && at==0x106E4)return board_words;
    assert(0);return 0;
}
void af_test_carried_board_original(void *p) {assert(p==&submenu_token);++load_calls;}
int af_carried_prior_name(u8 *out,u32 capacity,u32 item) {
    (void)out;(void)capacity;(void)item;++calls;return 7;
}
int af_carried_prior_type(u32 item) {(void)item;++calls;return 11;}
u32 af_carried_prior_price(u32 item) {(void)item;++calls;return 123;}
u16 af_carried_prior_display(u32 item) {++calls;return item;}
u16 af_carried_prior_pocket(u32 item) {++calls;return item;}
int af_carried_event_type(u32 item) {
    return item==0x2530 ? (event_mask&2 ? 47:0) : (event_mask&1 ? 45:0);
}
static u32 be(const u8 *p,u32 n) {u32 v=0;while(n--)v=(v<<8)|*p++;return v;}

int main(int argc,char **argv) {
    assert(argc==3);
    FILE *f=fopen(argv[1],"rb");assert(f);
    assert(!fseek(f,strtol(argv[2],0,0),SEEK_SET));
    u8 wire[sizeof(af_test_carried_header)];assert(fread(wire,1,sizeof(wire),f)==sizeof(wire));fclose(f);
    for(u32 i=0;i<8;i++)header[i]=be(wire+4*i,4);
    assert(header[0]==0x41464350 && header[2]==26 && header[3]==32 && !header[4] && !header[5]);
    AFCarryItem *rows=(AFCarryItem *)(header+8);
    for(u32 i=0;i<AF_CARRY_COUNT;i++) {
        const u8 *p=wire+32+i*32;AFCarryItem *r=rows+i;
        r->item=be(p,2);r->source=be(p+2,2);r->parent=be(p+4,2);
        r->family=p[6];r->state=p[7];r->category=p[8];r->reserved=p[9];
        r->price=be(p+10,2);r->icon=be(p+12,4);memcpy(r->name,p+16,16);
    }
    u8 out[18];memset(out,0xA5,sizeof(out));
    for(u32 i=0;i<AF_CARRY_COUNT;i++) {
        const AFCarryItem *r=rows+i;u32 mask=1u<<r->family;
        assert(af_carried_reserved(r->item));assert(!af_carried_type(r->item));
        assert(!af_carried_name(out+1,16,r->item));assert(!af_carried_icon(r->item));
        assert(!af_carried_display(r->item));assert(!af_carried_pocket(r->item));
        assert(!af_carried_price(r->item));assert(!af_carried_quantity(r->item));
        header[4]=mask;assert(!af_carried_type(r->item));header[5]=mask;
        if(r->family==2 || r->family==3)assert(!af_carried_type(r->item));
        event_mask=3;
        assert(af_carried_type(r->item)==r->category);
        assert(af_carried_category(r->item)==r->category);
        assert(af_carried_name(out+1,16,r->item)==1 && !memcmp(out+1,r->name,16));
        assert(out[0]==0xA5 && out[17]==0xA5);
        assert(!af_carried_name(0,16,r->item) && !af_carried_name(out,15,r->item));
        assert(af_carried_price(r->item)==r->price && af_carried_icon(r->item)==r->icon);
        assert(af_carried_display(r->item)==r->item && af_carried_pocket(r->item)==r->item);
        u32 max=r->family==0 ? 4 : r->family==6 ? 5 : 0;
        assert(af_carried_quantity(r->item)==(max ? r->state+1u : 0u));
        for(u32 q=0;q<=6;q++)assert(af_carried_with_quantity(r->item,q)==(q && q<=max ? r->parent+q-1u : 0));
        for(u32 j=0;j<AF_CARRY_COUNT;j++)if(rows[j].family!=r->family)assert(!af_carried_type(rows[j].item));
        header[4]=header[5]=event_mask=0;
    }
    assert(calls==0);
    const u16 native[]={0x2000,0x2003,0x203F,0x251D,0x2806,0x2901,0x2909,0x2B10,0x2D20,0x2D27};
    for(u32 i=0;i<sizeof(native)/sizeof(*native);i++) {
        u16 item=native[i];assert(!af_carried_reserved(item));assert(af_carried_category(item)==-1);
        assert(af_carried_name(out,16,item)==7 && af_carried_type(item)==11);
        assert(af_carried_price(item)==123 && af_carried_display(item)==item && af_carried_pocket(item)==item);
    }
    assert(calls==5*sizeof(native)/sizeof(*native));
    header[4]=header[5]=127;event_mask=3;
    for(u32 i=0;i<8;i++) {
        u32 saved=header[i];header[i]=0xFFFFFFFF;assert(!af_carried_type(rows[0].item));header[i]=saved;
    }
    AFCarryItem saved=rows[0];
    rows[0].family=7;assert(!af_carried_type(saved.item));rows[0]=saved;
    rows[0].state=4;assert(!af_carried_type(saved.item));rows[0]=saved;
    rows[0].icon=AF_CARRY_ICON_END;assert(!af_carried_type(saved.item));rows[0]=saved;
    rows[0].icon++;assert(!af_carried_type(saved.item));rows[0]=saved;
    rows[0].parent++;assert(!af_carried_type(saved.item));rows[0]=saved;
    u8 *board=(u8 *)board_words;
    for(u32 style=0;style<64;style++) {
        memset(board,0xA5,sizeof(board_words));board[0x31]=style;
        af_carried_board_load(&submenu_token);assert(board[0x31]==style);
        assert(board_words[0xB8/4]==0xA5A5A5A5);
    }
    assert(load_calls==64);
    for(u32 qty=0;qty<4;qty++) {
        memset(board,0xA5,sizeof(board_words));board[0x31]=64+qty;board[4]=1;
        u8 expected[sizeof(board_words)];memcpy(expected,board,sizeof(expected));
        expected[0x31]=64;
        af_carried_board_load(&submenu_token);
        assert(!memcmp(expected,board,sizeof(expected)));
        board[4]=0;af_carried_board_load(&submenu_token);assert(board[0x31]==64);
    }
    af_carried_board_load(0);assert(load_calls==64);
    board[0x31]=3;af_carried_board_load(&submenu_token);assert(load_calls==65);
    assert(board_words[0xB8/4]==0xA5A5A5A5);
    puts("Complete carried families, quantity readers, independent admission, predecessor delegation, and bounds pass");
    puts("All native paper loaders delegate; imported quantity/style normalization and resident artwork preserve adjacent letter fields");
}
