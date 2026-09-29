/* Actual shared policy/readers, independent of Wisp and content selection. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "carried_paper.h"
#include "holiday_cards.h"
#include "../overlays/v3/carried_catalogue.c"
#ifndef TEST_PAPER_MODE
#error Supply a concrete ROM-build mode
#endif
const AFCarryWord af_carried_paper_mode=TEST_PAPER_MODE;
AFCarryWord af_test_carried_header[8+8*AF_CARRY_COUNT];
static unsigned named,priced,recorded,owned;
int af_carried_prior_name(unsigned char *out,unsigned capacity,unsigned item) {
    assert(out && capacity==16 && item>=0x2000 && item<0x2040);
    memset(out,'x',16);named=item;return 1;
}
int af_carried_prior_type(unsigned item) {return item>=0x2000 && item<0x2040?17:0;}
unsigned af_carried_prior_price(unsigned item) {priced=item;return 40;}
unsigned short af_carried_prior_display(unsigned item) {return item;}
unsigned short af_carried_prior_pocket(unsigned item) {return item;}
int af_carried_event_type(unsigned item) {(void)item;return 0;}
void af_carried_prior_record(unsigned item) {recorded=item;}
int af_carried_prior_owned(const unsigned char *player,unsigned item) {(void)player;owned=item;return 1;}
unsigned char af_console_players[4*0xBD0],*af_test_carried_active;
static unsigned selected_category,selected_count,prior_goods,prior_shop,preview_native;
static unsigned short selection[68];
void af_paper_original_select(void *game,unsigned short *items,int count,
        unsigned short *existing,int existing_count,int category,int list) {
    assert(game==&selected_count && existing==selection && existing_count==3 && list==8);
    selected_category=category;selected_count++;
    if(items && count>0)memcpy(items,selection,(unsigned)count*2);
}
int af_paper_original_goods_exist(unsigned short *items,int count,unsigned item) {
    prior_goods++;
    for(int i=0;items && i<count;i++)if(items[i]==(unsigned short)item)return 1;
    return 0;
}
int af_paper_prior_shop_category(unsigned item) {prior_shop=item;return 21;}
int af_carried_prior_catalogue_bit(const u32 *bits,int index,NativeBit native) {return native(bits,index);}
int af_carried_owned(const unsigned char *,unsigned);
void af_test_carried_paper_init(PaperPreview *p,unsigned item) {
    preview_native=item;p->style=item-0x2000;p->price=40;p->type=1;
}
static unsigned char cards[48];
unsigned af_test_carried_profile[8],af_test_event_item_profile;
unsigned char *af_v3_card_data(void) {return cards;}
void af_v3_save_halt(int reason) {assert(!reason);__builtin_trap();}
extern int af_carried_name(unsigned char *,unsigned,unsigned),af_carried_type(unsigned);
extern unsigned af_carried_price(unsigned),af_carried_icon(unsigned);
extern unsigned short af_carried_display(unsigned),af_carried_pocket(unsigned);
extern void af_carried_record(unsigned);
extern int af_carried_owned(const unsigned char *,unsigned);
extern int af_carried_menu_type(void *,unsigned,int);
extern void af_carried_grab_one(void *,void *),af_carried_drop_stack(void *,void *,unsigned short *,int);
extern void af_carried_consume_paper(void *,int,unsigned,int);
static unsigned submenu_token,overlay_token,tag[128],hand[200];
unsigned char *af_test_carried_action_active=af_console_players;
#define H(p,o) (*(unsigned short *)((unsigned char *)(p)+(o)))
#define W(p,o) (*(unsigned *)((unsigned char *)(p)+(o)))
void *af_test_carried_action_pointer(void *p,unsigned at) {
    if(p==&submenu_token && at==0x2C)return &overlay_token;
    if(p==&overlay_token && at==0x106D0)return tag;
    if(p==&overlay_token && at==0x106D4)return hand;
    assert(0);return 0;
}
int af_carried_prior_menu(void *p,unsigned item,int slot) {
    assert(p==&submenu_token && slot==0);
    assert(item>=0x2000 && item<0x2044);return 3;
}
static int pocket(void *p) {assert(p==(unsigned char *)tag+8);return 0;}
static int close_menu(void *p,int a,int b) {assert(p==&submenu_token && !a && !b);return 1;}
static void refresh(void *p) {assert(p==&submenu_token);}
static void sound(int id) {assert(id==0x33);}
static void swap(void *sub,void *t,unsigned short *target,void *mail) {
    assert(sub==&submenu_token && t==tag && !mail);
    unsigned short old=*target;*target=H(hand,0x23C);H(hand,0x23C)=old;
}
static void ordinary(void *sub,void *t,unsigned short *target,int slot) {
    assert(!slot);swap(sub,t,target,0);
}
static void set(void *p,int slot,unsigned item,int cond) {
    assert(p==af_console_players && !slot && !cond);H(p,0x14)=item;
}
void *af_test_carried_action_function(unsigned at) {
    switch(at) {
    case 0x8086F910:return pocket;
    case 0x8086F4AC:return close_menu;
    case 0x8086FD3C:return refresh;
    case 0x800D1A9C:return sound;
    case 0x8087A94C:return swap;
    case 0x8087AC90:return ordinary;
    case 0x800B8B08:return set;
    default:assert(0);return 0;
    }
}
static void actions(void) {
    if(TEST_PAPER_MODE>1)return;
    unsigned short *target=(unsigned short *)(af_console_players+0x14);
    for(unsigned style=0;style<=64;style++) {
        unsigned single=style==64?0x2040:0x2000+style;
        if(TEST_PAPER_MODE==0) {
            *target=single;H(hand,0x23C)=single;
            assert(af_carried_menu_type(&submenu_token,single,0)==3);
            af_carried_drop_stack(&submenu_token,tag,target,0);
            assert(*target==single && H(hand,0x23C)==single);
            af_carried_consume_paper(af_console_players,0,0,0);assert(!*target);
            continue;
        }
        *target=af_carried_paper_with_quantity(single,4);H(hand,0x23C)=0;
        assert(af_carried_menu_type(&submenu_token,*target,0)==47);
        af_carried_grab_one(&submenu_token,0);
        assert(H(hand,0x23C)==single && af_carried_paper_quantity(*target)==3);
        /* A pair of three-sheet packs leaves four in the pocket and two in hand. */
        H(hand,0x23C)=*target;
        af_carried_drop_stack(&submenu_token,tag,target,0);
        assert(af_carried_paper_quantity(*target)==4 && af_carried_paper_quantity(H(hand,0x23C))==2);
        for(unsigned q=4;q;q--) {
            assert(af_carried_paper_quantity(*target)==q);
            af_carried_consume_paper(af_console_players,0,0,0);
        }
        assert(!*target);
    }
}

static void supply(void) {
    unsigned short generated[68];
    for(unsigned i=0;i<64;i++)selection[i]=0x2000+i;
    selection[64]=0x2043;selection[65]=0;selection[66]=0xFFFF;selection[67]=0x1008;
    af_carried_paper_select(&selected_count,generated,68,selection,3,1,8);
    assert(selected_count==1 && selected_category==1);
    for(unsigned style=0;style<65;style++) {
        unsigned q=af_carried_paper_obtain(style==64?0x2040:0x2000+style);
        assert(generated[style]==q);
        assert(af_carried_paper_catalogue_item(style==64?67:style)==q);
        assert(selection[style]==(style==64?0x2043:0x2000+style));
        if(TEST_PAPER_MODE<2) {
            PaperPreview p;memset(&p,0xAB,sizeof(p));preview_native=0;
            af_carried_paper_init(&p,q);
            assert(p.style==style && p.type==1 && p.price==(TEST_PAPER_MODE?160u:40u));
            if(style<64)assert(preview_native==0x2000+style);
            else assert(!preview_native && p.buffer==0xABABABAB);
        }
    }
    assert(!generated[65] && generated[66]==0xFFFF && generated[67]==0x1008);
    assert(!af_carried_paper_catalogue_item(64) && !af_carried_paper_catalogue_item(66));
    assert(!af_carried_paper_catalogue_item(68));
    af_carried_paper_select(&selected_count,generated,68,selection,3,0,8);
    assert(selected_count==2 && !selected_category && !memcmp(generated,selection,sizeof(selection)));
    af_carried_paper_select(&selected_count,0,0,selection,3,1,8);
    assert(selected_count==3);
    unsigned short existing[]={0x2EC5,0x2E87,0x2042,0x1008};
    unsigned short before[4];memcpy(before,existing,sizeof(before));
    for(unsigned style=0;style<65;style++) {
        unsigned item=style<64?0x2000+style:0x2040;
        int wanted=TEST_PAPER_MODE==1 && (style==5 || style==7 || style==64);
        unsigned old=prior_goods;
        assert(af_carried_paper_goods_exist(existing,4,item)==wanted);
        assert(prior_goods==old+(TEST_PAPER_MODE!=1));
    }
    assert(!memcmp(existing,before,sizeof(before)));
    assert(af_carried_paper_goods_exist(existing,4,0x1008)==1);
    assert(!af_carried_paper_goods_exist(0,4,0x2005));
    assert(!af_carried_paper_goods_exist(existing,-1,0x2005));
    assert(af_carried_paper_shop_category(0x2EC5)==(TEST_PAPER_MODE==1?1:-1));
    assert(af_carried_paper_shop_category(0x2043)==1);
    assert(af_carried_paper_shop_category(0x2E00)==21 && prior_shop==0x2E00);
}

int main(void) {
    unsigned *h=af_test_carried_header;
    h[0]=0x41464350;h[1]=1;h[2]=AF_CARRY_COUNT;h[3]=sizeof(AFCarryItem);
    AFCarryItem *rows=(AFCarryItem *)(h+8);
    for(unsigned q=1;q<=4;q++) {
        rows[q-1]=(AFCarryItem){.item=0x203F+q,.source=0x2003+(q-1)*64,
            .parent=0x2040,.family=0,.state=q-1,.category=49,.price=q*40,
            .icon=AF_CARRY_ICON+(q-1)*576};
        memset(rows[q-1].name,'x',16);
    }
    unsigned char name[16];
    for(unsigned style=0;style<64;style++) {
        unsigned single=0x2000+style;
        assert(af_carried_paper_obtain(single)==(TEST_PAPER_MODE==1?
            AF_PAPER_PACK_FIRST+128+style:TEST_PAPER_MODE==0?single:0));
        for(unsigned q=1;q<=4;q++) {
            unsigned item=af_carried_paper_with_quantity(single,q);
            assert(item && af_carried_paper_style(item)==(int)style);
            assert(af_carried_paper_quantity(item)==q);
            assert(af_carried_paper_with_quantity(item,1)==single);
            assert(!af_carried_paper_with_quantity(item,0) && !af_carried_paper_with_quantity(item,5));
            assert(af_cw_paper_stack(item,q)==af_carried_paper_obtain(single));
            if(q==1)continue;
            assert(af_carried_reserved(item));
            if(TEST_PAPER_MODE==1) {
                assert(af_carried_type(item)==17 && af_carried_quantity(item)==q);
                assert(af_carried_with_quantity(item,1)==single);
                assert(af_carried_name(name,16,item)==1 && named==single);
                assert(af_carried_price(item)==40*q && priced==single);
                assert(af_carried_icon(item)==AF_CARRY_ICON+(q-1)*576);
                assert(af_carried_display(item)==item && af_carried_pocket(item)==item);
                af_carried_record(item);assert(recorded==single);
                assert(af_carried_owned(af_console_players,item) && owned==single);
            } else {
                assert(!af_carried_type(item) && !af_carried_quantity(item));
                assert(!af_carried_with_quantity(item,1));
                assert(!af_carried_name(name,16,item) && !af_carried_price(item));
                assert(!af_carried_icon(item) && !af_carried_display(item) && !af_carried_pocket(item));
                assert(!af_carried_owned(af_console_players,item));
            }
        }
    }
    /* Original-paper pack mode neither needs nor enables orange stationery. */
    assert(!h[4] && !h[5] && !af_carried_paper_obtain(0x2043));
    h[4]=h[5]=1;
    for(unsigned q=1;q<=4;q++) {
        assert(af_carried_paper_style(0x203F+q)==64);
        assert(af_carried_paper_obtain(0x203F+q)==(TEST_PAPER_MODE==1?0x2043:TEST_PAPER_MODE==0?0x2040:0));
        assert(af_cw_paper_stack(0x203F+q,q)==af_carried_paper_obtain(0x2040));
    }
    actions();supply();
    for(unsigned i=0;i<65536;i++)if(!(i>=0x2000 && i<0x2044) && !af_carried_paper_reserved(i)) {
        assert(af_carried_paper_style(i)<0 && !af_carried_paper_quantity(i));
        assert(!af_carried_paper_obtain(i) && !af_cw_paper_stack(i,4));
    }
    assert(!af_cw_paper_stack(0x2000,0) && !af_cw_paper_stack(0x2000,5));
    /* Save binding is conservative and transactional. A pack-dependent save
     * cannot silently lose sheets when opened with single-sheet behaviour. */
    af_holiday_cards_reset(cards);
    AFHolidayCard stamp={{2001,7,25},3};
    assert(af_holiday_cards_set(cards,2,&stamp));
    cards[4]=4;cards[8]=64;cards[13]=9;cards[14]=29;
    unsigned char before[48];memcpy(before,cards,48);
    if(TEST_PAPER_MODE<2) {
        assert(af_carried_save_bind(cards,0,64));
        assert(cards[4]==5 && cards[15]==TEST_PAPER_MODE);
        assert(af_carried_quest_day(cards)==0x091D);
        assert(!memcmp(cards+16,before+16,32));
        AFHolidayCard read;assert(af_holiday_cards_get(cards,2,&read));
        assert(read.days==3 && read.last_date.year==2001);
        assert(af_holiday_cards_clear(cards,2) && cards[15]==TEST_PAPER_MODE);
        cards[15]=1;memcpy(before,cards,48);
        assert(af_carried_save_bind(cards,0,64)==(TEST_PAPER_MODE==1));
        if(TEST_PAPER_MODE==0)assert(!memcmp(before,cards,48));
        cards[15]=2;assert(!af_holiday_cards_valid(cards));
    } else {
        assert(!af_carried_save_bind(cards,0,64));
        assert(!memcmp(cards,before,48));
    }
    puts("global stationery policy, all styles/quantities, shared readers, and independent selection pass");
}
