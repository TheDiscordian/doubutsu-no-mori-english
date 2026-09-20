#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/balloon_menu.c"

static alignas(16) u8 private_data[0x400],submenu[0x100],menu[0x80],overlay[16],tag[0x100],game[16];
u8 *af_test_balloon_menu_active=private_data,af_test_balloon_menu_field;
void *af_test_balloon_menu_game=game;
static int selected=255,accepted=1,slot=0,fallbacks,queued,warnings,steps,missing;
static u32 item_seen,replace_seen;
static void *submenu_seen;
static int slot_seen;
void *af_test_balloon_menu_pointer(void *p,u32 at) {
    if(p==submenu && at==0x2C)return missing==1?0:overlay;
    assert(p==overlay && at==0x106D0);return missing==2?0:tag;
}
int af_v3_player_selected_equipment(u32 item) {
    u32 shape=item-0x2244u;
    return shape<8u && (selected&(1u<<shape))?(int)(91+shape):-1;
}
int af_v3_balloon_queue(void *g,u32 item,int flag) {
    assert(g==game && !flag && !steps);queued++;item_seen=item;
    if(!accepted || af_v3_player_selected_equipment(item)<0)return 0;
    steps=1;return 1;
}
static int fallback(void *s,u32 item,int index) {
    fallbacks++;submenu_seen=s;item_seen=item;slot_seen=index;return 123;
}
static int index_of(void *p) {assert(p==tag+8);return slot;}
static void warn(void *s,void *m,int kind) {assert(s==submenu && m==menu && kind==11 && !steps);warnings++;}
static void pocket(void *p,int index,u32 replacement,int condition) {
    assert(p==private_data && index==slot && !condition && steps==1);
    assert(submenu[0xDF]==slot && HALF(submenu,0xE0)==item_seen);
    replace_seen=replacement;HALF(p,0x14+index*2)=(u16)replacement;steps=2;
}
static int return_tag(void *s,int a,int b) {assert(s==submenu && !a && !b && steps==2);steps=3;return 0;}
static void close_tag(void *s,void *m,int direction) {assert(s==submenu && m==menu && direction==1 && steps==3);steps=4;}
void *af_test_balloon_menu_function(u32 at) {
    switch(at) {
    case 0x80875610:return fallback;
    case 0x8086F910:return index_of;
    case 0x80871570:return warn;
    case 0x800B8B08:return pocket;
    case 0x8086F4AC:return return_tag;
    case 0x80871760:return close_tag;
    default:assert(!"Unexpected balloon menu API");return 0;
    }
}
int main(void) {
    for(int shape=0;shape<8;shape++) for(int field=0;field<4;field++) for(int condition=0;condition<4;condition++) {
        slot=shape*2; if(slot==16)slot=14;
        WORD(private_data,0x34)=(u32)condition<<(slot*2);af_test_balloon_menu_field=(u8)field;
        int prior=fallbacks;
        assert(af_v3_balloon_menu_type(submenu,0x2244+shape,slot)==(condition?123:field==0?44:field==1?12:8));
        assert(fallbacks==prior+(condition!=0));
        selected=255^(1<<shape);assert(af_v3_balloon_menu_type(submenu,0x2244+shape,slot)==123);selected=255;
    }
    WORD(private_data,0x34)=0;
    for(int index=-1;index<17;index++) if(index<0 || index>=15) {
        assert(af_v3_balloon_menu_type(submenu,0x2244,index)==123);
        assert(submenu_seen==submenu && slot_seen==index && item_seen==0x2244);
    }
    for(u32 item=0x2243;item<=0x224C;item+=9)assert(af_v3_balloon_menu_type(submenu,item,0)==123);
    af_test_balloon_menu_active=0;assert(af_v3_balloon_menu_type(submenu,0x2244,0)==123);af_test_balloon_menu_active=private_data;
    af_test_balloon_menu_field=0;
    for(int shape=0;shape<8;shape++) for(int exchange=0;exchange<2;exchange++) for(accepted=0;accepted<2;accepted++) {
        slot=shape*2;steps=queued=warnings=0;
        memset(submenu,0xA5,sizeof(submenu));memset(private_data,0xA5,sizeof(private_data));WORD(private_data,0x34)=0;
        HALF(private_data,0x14+slot*2)=(u16)(0x2244+shape);WORD(menu,0x38)=exchange?13:0;WORD(menu,0x3C)=0xAABB1234;
        u8 saved[sizeof(private_data)];memcpy(saved,private_data,sizeof(saved));
        af_v3_balloon_menu_fly(submenu,menu);
        assert(queued==1 && warnings==!accepted && steps==(accepted?4:0));
        if(accepted) {
            assert(replace_seen==(exchange?0x1234u:0u));HALF(saved,0x14+slot*2)=(u16)replace_seen;
            assert(submenu[0xDF]==slot && HALF(submenu,0xE0)==0x2244+shape);
            submenu[0xDF]=0xA5;HALF(submenu,0xE0)=0xA5A5;
        }
        assert(!memcmp(saved,private_data,sizeof(saved)));
        for(unsigned i=0;i<sizeof(submenu);i++)assert(submenu[i]==0xA5);
    }
    accepted=1;
    for(int failure=0;failure<12;failure++) {
        steps=queued=warnings=0;slot=0;missing=0;af_test_balloon_menu_field=0;
        af_test_balloon_menu_active=private_data;af_test_balloon_menu_game=game;WORD(private_data,0x34)=0;
        HALF(private_data,0x14)=0x2244;selected=255;
        if(failure==2)af_test_balloon_menu_active=0;
        if(failure==3)af_test_balloon_menu_field=1;
        if(failure==4)af_test_balloon_menu_game=0;
        if(failure==5 || failure==6)missing=failure-4;
        if(failure==7)slot=-1;
        if(failure==8)slot=15;
        if(failure==9)WORD(private_data,0x34)=1;
        if(failure==10)selected=254;
        if(failure==11)HALF(private_data,0x14)=0x1234;
        u8 saved[sizeof(private_data)];memcpy(saved,private_data,sizeof(saved));
        af_v3_balloon_menu_fly(failure==0?0:submenu,failure==1?0:menu);
        assert(!steps && queued==(failure>=10) && warnings==(failure>=10));
        assert(!memcmp(saved,private_data,sizeof(saved)));
    }
    puts("shared balloon menu classification, transfer, and rejection pass");
}
