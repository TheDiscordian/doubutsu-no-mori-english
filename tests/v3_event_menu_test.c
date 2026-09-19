#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/event_menu.c"

Category af_test_event_categories[3]={{0x2254,780,0x1758,8,0},
    {0x224C,680,0x1759,8,1},{0x2244,480,0x175A,8,2}};
static u8 owner_bytes[0x1270];
u8 *af_test_event_owner=owner_bytes;
static struct { u32 guard; Stock stock[2]; u32 end; } save;
static struct { u32 guard; Vendor actor; u32 end; } guarded;
static u8 masks[3],strings[4][16];
static int orders[6][10],pick,room,grant_ok,grants,payments,original_calls,random_calls;
static u32 bells,last_item,last_msg,last_demo,price_text;
static unsigned string_mask;
int af_test_event_selected(u32 item) {
    for (u32 k=0;k<3;k++) if (item>=categories[k].first && item<categories[k].first+8u)
        return masks[k]&(1u<<(item-categories[k].first)) ? 91+(int)(item-0x2244u) : -1;
    return -1;
}
float af_test_event_random(void) { ++random_calls;return 0.5f; }
u8 *af_test_event_get_area(u32 event,u32 id) {
    assert(event==11 && id==0);return (u8 *)save.stock;
}
void af_test_event_original(void) { assert(0); }
static int get_order(u32 group,u32 id) { assert(group<6 && id<10);return orders[group][id]; }
static void set_order(u32 group,u32 id,u32 value) { assert(group<6 && id<10);orders[group][id]=(int)value; }
static void *choice_window(void) { return strings; }
static void *msg_window(void) { return &last_msg; }
static int choice_index(void *window) { assert(window==strings);return pick; }
static void continue_msg(void *window,u32 value) { assert(window==&last_msg);last_msg=value; }
static void demo_msg(u32 value) { last_demo=value; }
static void camera(u32 value) { assert(value==9); }
static int free_count(void *priv,u32 empty) { assert(priv==&bells && !empty);return room; }
static int give_item(void *priv,u32 item,u32 condition) {
    assert(priv==&bells && !condition && room);
    if (!grant_ok) return 0;
    --room;++grants;last_item=item;return 1;
}
static int money_check(u32 price) { return bells>=price; }
static void payment(u32 price) { assert(bells>=price);bells-=price;++payments; }
static void price_string(u32 price,u32 slot) { assert(!slot);price_text=price; }
static int name(u8 *dest,u32 size,u32 item) {
    assert(size==16);memset(dest,' ',16);dest[0]=(u8)(item>>8);dest[1]=(u8)item;return 16;
}
static void set_choices(void *window,const u8 *a,int an,const u8 *b,int bn,
                        const u8 *c,int cn,const u8 *d,int dn) {
    assert(window==strings && an==16 && bn==16 && cn==16 && dn==16);
    const u8 *p[]={a,b,c,d};string_mask=0;
    for (u32 i=0;i<4;i++) {
        memset(strings[i],0,16);
        if (p[i]) { memcpy(strings[i],p[i],16);string_mask|=1u<<i; }
    }
}
static void native_stub(Vendor *vendor,void *game) { (void)vendor;(void)game;assert(0); }
static Action native_action(u32 i) { assert(i<6);return native_stub; }
static void native_info(Vendor *v) {
    ++original_calls;Stock *s=save.stock;int count=0;
    for (u32 i=0;i<8;i++) count+=!!s->goods[i];
    v->next=count ? (s->kind==2 ? 2u : 1u) : 4u;
    v->price=(const u32[]){980,1000,1280}[s->kind];v->start=0;
    demo_msg(count ? AF_V3_EVENT_NATIVE_FIRST+s->kind : 0x1757u);camera(9);
}
static Vendor *reset(u32 kind,u8 mask) {
    memset(&guarded,0,sizeof(guarded));memset(&save,0,sizeof(save));memset(orders,0,sizeof(orders));
    memset(masks,0,sizeof(masks));masks[kind]=mask;
    guarded.guard=save.guard=0x12345678;guarded.end=save.end=0x87654321;
    for (u32 i=0;i<8;i++) save.stock[0].goods[i]=(u16)(0x2600+i);
    save.stock[0].count=8;
    memcpy(owner_bytes+0x1250,"I'm not buying! ",16);memcpy(owner_bytes+0x1260,"I don't want it!",16);
    private_data=&bells;bells=10000;room=15;grant_ok=1;
    grants=payments=original_calls=random_calls=0;last_item=last_msg=last_demo=price_text=0;
    return &guarded.actor;
}
static void response(int choice) { pick=choice;orders[4][9]=1; }
static void enter_imports(Vendor *v) {
    af_v3_event_menu_start(v);
    assert(v->mode==2 && v->next==6 && last_demo==AF_V3_EVENT_ROUTE_MESSAGE);
    assert(string_mask==7 && !memcmp(strings[0],"Original wares  ",16));
    assert(!memcmp(strings[1],"Festival items  ",16));
    af_v3_event_menu_setup(v,6);assert(v->proc==(u32)(uptr)af_v3_event_menu_route);
    response(1);af_v3_event_menu_route(v,0);assert(v->mode==1 && v->action==1);
    assert(last_msg==categories[save.stock[1].kind].message);
    response(0);af_v3_event_menu_select(v,0);assert(v->action==3 && price_text==v->price);
}
int main(void) {
    Vendor *v=reset(0,0);Stock native=save.stock[0];
    af_v3_event_menu_start(v);assert(original_calls==1 && v->mode==0 && !random_calls);
    for (int action=0;action<6;action++) {
        af_v3_event_menu_setup(v,action);assert(v->action==(u32)action && v->proc==(u32)(uptr)native_stub);
    }
    af_v3_event_menu_setup(v,-1);assert(v->action==4);
    v=reset(0,0xFF);af_v3_event_menu_start(v);
    response(0);af_v3_event_menu_route(v,0);
    assert(original_calls==1 && v->mode==0 && v->price==980 && last_msg==AF_V3_EVENT_NATIVE_FIRST);
    save.stock[0].kind=2;af_v3_event_menu_start(v);response(0);af_v3_event_menu_route(v,0);
    assert(v->next==2 && v->action==2 && v->price==1280 && v->proc==(u32)(uptr)native_stub);
    af_v3_event_menu_start(v);response(2);af_v3_event_menu_route(v,0);assert(v->action==4 && last_msg==0x175B);
    /* Sparse pages use saved slots, not compacted identities. */
    v=reset(0,0xA5);enter_imports(v);
    assert(v->next_start==6 && last_msg==0x1762 && string_mask==15);
    assert(strings[0][1]==0x54 && strings[1][1]==0x56 && strings[2][1]==0x59);
    response(3);af_v3_event_menu_purchase(v,0);assert(v->start==6 && v->action==1 && last_msg==0x1767);
    response(0);af_v3_event_menu_select(v,0);assert(v->next_start==8 && last_msg==0x1761 && string_mask==3);
    assert(strings[0][1]==0x5B && !memcmp(strings[1],owner_bytes+0x1250,16));
    response(1);af_v3_event_menu_purchase(v,0);assert(v->action==4 && last_msg==0x1763 && !grants && !payments);
    /* Every failed transaction retains money, stock, and original merchandise. */
    for (u32 failure=0;failure<5;failure++) {
        v=reset(0,1);enter_imports(v);Stock retained=save.stock[1];u32 before=bells;
        if (failure==0) room=0;
        if (failure==1) before=bells=779;
        if (failure==2) grant_ok=0;
        if (failure==3) v->price++;
        if (failure==4) private_data=0;
        response(0);af_v3_event_menu_purchase(v,0);
        assert(!grants && !payments && bells==before && !memcmp(&retained,save.stock+1,sizeof(Stock)));
        assert(!memcmp(&native,save.stock,sizeof(Stock)) && v->action==4);
    }
    for (u32 kind=0;kind<3;kind++) {
        v=reset(kind,0x81);enter_imports(v);u32 price=categories[kind].price;
        response(1);af_v3_event_menu_purchase(v,0);
        assert(grants==1 && payments==1 && bells==10000-price && last_item==categories[kind].first+7u);
        assert(v->action==5 && v->next==0 && last_msg==0x1764 && !save.stock[1].goods[7]);
        af_v3_event_menu_purchase(v,0);assert(grants==1 && payments==1); /* Same order cannot repeat. */
        orders[4][1]=2;af_v3_event_menu_give(v,0);
        assert(v->action==0 && orders[5][0]==(int)last_item && orders[5][1]==7 && !orders[5][2]);
        assert(last_msg==0x1766);af_v3_event_menu_setup(v,1); /* Native wait continuation. */
        response(0);af_v3_event_menu_select(v,0);response(0);af_v3_event_menu_purchase(v,0);
        assert(grants==2 && payments==2 && bells==10000-2*price && v->next==4 && v->action==5);
        af_v3_event_menu_give(v,0);assert(v->action==4 && last_msg==0x1760);
        assert(save.stock[1].count==8 && stock_count(save.stock+1,0)==0);
        af_v3_event_menu_start(v);response(1);af_v3_event_menu_route(v,0);
        assert(last_msg==0x1757 && v->action==4 && grants==2 && random_calls==1);
        assert(!memcmp(&native,save.stock,sizeof(Stock)));
    }
    assert(guarded.guard==0x12345678 && guarded.end==0x87654321 && save.guard==0x12345678 && save.end==0x87654321);
    puts("Shared original/imported routes, sparse pages, transaction failures, prices, handover, and finite stock pass");
}
