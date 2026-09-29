#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/carried_items.c"
#include "../overlays/v3/carried_menu.c"
#define AF_CARRIED_PAPER_MENUS 47
#include "../overlays/v3/carried_actions.c"

u32 af_test_carried_header[8+8*AF_CARRY_COUNT];
static u32 calls,event_mask;
static u32 board_words[48],overlay_token,submenu_token,load_calls;
void *af_test_carried_menu_pointer(void *p,u32 at) {
    if(p==&submenu_token && at==0x2C)return &overlay_token;
    if(p==&overlay_token && at==0x106E4)return board_words;
    assert(0);return 0;
}
void af_test_carried_board_original(void *p) {assert(p==&submenu_token);++load_calls;}
static u32 action_player[300],action_hand[200],action_tag[90];
u8 *af_test_carried_action_active=(u8 *)action_player;
static int action_slot,prior_menu,return_calls,refresh_calls,sounds,drop_calls,ordinary_drops,set_calls;
void *af_test_carried_action_pointer(void *p,u32 at) {
    if(p==&submenu_token && at==0x2C)return &overlay_token;
    if(p==&overlay_token && at==0x106D0)return action_tag;
    if(p==&overlay_token && at==0x106D4)return action_hand;
    assert(0);return 0;
}
int af_carried_prior_menu(void *sub,u32 item,int slot) {
    assert(sub==&submenu_token);(void)item;(void)slot;return prior_menu;
}
static int slot_stub(void *tag) {assert(tag==(u8 *)action_tag+8);return action_slot;}
static int return_stub(void *sub,int type,int mode) {
    assert(sub==&submenu_token && !type && !mode);++return_calls;return 1;
}
static void refresh_stub(void *sub) {assert(sub==&submenu_token);++refresh_calls;}
static void sound_stub(int id) {assert(id==0x33);++sounds;}
static void drop_stub(void *sub,void *tag,u16 *target,void *mail) {
    assert(sub==&submenu_token && tag==action_tag && !mail);++drop_calls;
    u16 rest=*target;*target=H(action_hand,0x23C);H(action_hand,0x23C)=rest;
}
static void ordinary_drop_stub(void *sub,void *tag,u16 *target,int slot) {
    assert(slot==action_slot);++ordinary_drops;drop_stub(sub,tag,target,0);
}
static void set_stub(void *player,int slot,u32 item,int cond) {
    assert(player==action_player && (u32)slot<15u);++set_calls;
    H(player,0x14+slot*2)=item;
    W(player,0x34)=(W(player,0x34)&~(3u<<(slot*2)))|((u32)cond<<(slot*2));
}
void *af_test_carried_action_function(u32 at) {
    switch(at) {
        case 0x8086F910:return slot_stub;
        case 0x8086F4AC:return return_stub;
        case 0x8086FD3C:return refresh_stub;
        case 0x800D1A9C:return sound_stub;
        case 0x8087A94C:return drop_stub;
        case 0x8087AC90:return ordinary_drop_stub;
        case 0x800B8B08:return set_stub;
        default:assert(0);return 0;
    }
}

static void stack_actions(void) {
    memset(action_player,0,sizeof(action_player));memset(action_hand,0,sizeof(action_hand));
    header[4]=header[5]=127;event_mask=3;action_slot=7;
    const int original[]={3,4,15,17};
    for(u32 q=1;q<=4;q++)for(int context=0;context<4;context++) {
        prior_menu=original[context];
        assert(af_carried_menu_type(&submenu_token,0x203F+q,7)==(q>1?47+context:prior_menu));
        assert(af_carried_menu_type(&submenu_token,0x2003,7)==prior_menu);
        W(action_player,0x34)=1u<<14;
        assert(af_carried_menu_type(&submenu_token,0x203F+q,7)==prior_menu);
        W(action_player,0x34)=0;header[5]=0;
        assert(af_carried_menu_type(&submenu_token,0x203F+q,7)==prior_menu);header[5]=127;
    }
    for(prior_menu=0;prior_menu<47;prior_menu++) {
        if(prior_menu==3 || prior_menu==4 || prior_menu==15 || prior_menu==17)continue;
        assert(af_carried_menu_type(&submenu_token,0x2043,7)==prior_menu);
    }
    for(u32 family=0;family<2;family++) {
        u32 parent=family?0x2D28:0x2040,max=family?5:4;
        for(u32 a=1;a<=max;a++)for(u32 b=1;b<=max;b++) {
            u16 *target=(u16 *)((u8 *)action_player+0x14+action_slot*2);
            *target=parent+b-1;H(action_hand,0x23C)=parent+a-1;
            int previous=ordinary_drops;
            af_carried_drop_stack(&submenu_token,action_tag,target,action_slot);
            if(a<max && b<max) {
                assert(ordinary_drops==previous);
                assert(*target==parent+(a+b>max?max:a+b)-1);
                assert(H(action_hand,0x23C)==(a+b>max?parent+a+b-max-1:0));
            } else {
                assert(ordinary_drops==previous+1);
                assert(*target==parent+a-1 && H(action_hand,0x23C)==parent+b-1);
            }
        }
        for(u32 q=2;q<=max;q++) {
            H(action_player,0x14+14)=parent+q-1;H(action_hand,0x23C)=0;
            u32 player_before[300];memcpy(player_before,action_player,sizeof(player_before));
            af_carried_grab_one(&submenu_token,0);
            assert(H(action_hand,0x23C)==parent && H(action_hand,0x23A)==2);
            assert(!W(action_hand,0x2E4) && ((u8 *)action_hand)[0x2E8]==0);
            assert(((u8 *)action_hand)[0x2E9]==7 && ((u8 *)action_hand)[0x2EB]==0);
            H(player_before,0x14+14)=parent+q-2;
            assert(!memcmp(player_before,action_player,sizeof(player_before)));
        }
    }
    assert(return_calls==7 && refresh_calls==7 && sounds==7);
    /* Independent families and protected targets must never merge. */
    for(u32 mode=0;mode<4;mode++) {
        H(action_player,0x22)=mode==0?0x2D28:0x2040;H(action_hand,0x23C)=0x2040;
        W(action_player,0x34)=mode==1?2u<<14:0;W(action_hand,0x2E4)=mode==2?1:0;
        if(mode==3)header[5]=0;
        int previous=ordinary_drops;
        af_carried_drop_stack(&submenu_token,action_tag,(u16 *)((u8 *)action_player+0x22),7);
        assert(ordinary_drops==previous+1);header[5]=127;
    }
    W(action_player,0x34)=W(action_hand,0x2E4)=0;
    for(u32 q=1;q<=4;q++) {
        H(action_player,0x22)=0x203F+q;
        af_carried_consume_paper(action_player,7,0,0);
        assert(H(action_player,0x22)==(q==1?0:0x203Eu+q));
    }
    for(u32 style=0;style<64;style++) {
        H(action_player,0x22)=0x2000+style;af_carried_consume_paper(action_player,7,0,0);
        assert(!H(action_player,0x22));
    }
    H(action_player,0x22)=0x2043;header[5]=0;
    af_carried_consume_paper(action_player,7,0,0);assert(H(action_player,0x22)==0x2043);
    assert(set_calls==68);header[5]=127;
    /* Occupied hands, singletons, protected pockets, and invalid slots do not
     * split or alter the adjacent player record. */
    for(u32 mode=0;mode<5;mode++) {
        action_slot=mode==4?15:7;H(action_player,0x22)=mode==1?0x2040:0x2043;
        H(action_hand,0x23C)=mode==0?0x2001:0;W(action_player,0x34)=mode==2?2u<<14:0;
        if(mode==3)header[5]=0;
        u32 saved_player[300],saved_hand[200];
        memcpy(saved_player,action_player,sizeof(saved_player));memcpy(saved_hand,action_hand,sizeof(saved_hand));
        af_carried_grab_one(&submenu_token,0);
        assert(!memcmp(saved_player,action_player,sizeof(saved_player)));
        assert(!memcmp(saved_hand,action_hand,sizeof(saved_hand)));header[5]=127;
    }
    puts("Paper/spirit stack merging and splitting, protected-item delegation, native menu contexts, and confirmed one-sheet consumption pass");
}
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
    stack_actions();
    puts("Complete carried families, quantity readers, independent admission, predecessor delegation, and bounds pass");
    puts("All native paper loaders delegate; imported quantity/style normalization and resident artwork preserve adjacent letter fields");
}
