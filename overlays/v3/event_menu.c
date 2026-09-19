/* Additive festival merchandise: retain native wares and their transaction
   callbacks, while the imported route consumes its separate event stock. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct { u16 goods[8], count, kind; } Stock;
typedef struct { u16 item, price, message, slot; } Offer;
typedef struct { u16 first, price, message; u8 count, kind; } Category;
typedef struct {
    u8 prefix[0x938];
    u32 proc, action, next;
    u16 item;
    s16 start, next_start;
    u16 pad;
    u32 price;
    s16 dst_x,dst_z;
    u32 mode;
} Vendor;
typedef void (*Action)(Vendor *,void *);
_Static_assert(__builtin_offsetof(Vendor,mode)==0x954, "Appended vendor mode");
_Static_assert(sizeof(Vendor)==0x958, "Native vendor allocation");
#ifdef __mips__
#define owner (*(u8 **)0x80101BC0u)
#define private_data (*(void **)0x80136FD8u)
#define get_area ((Stock *(*)(u32,u32))0x8008033Cu)
#define get_order ((int (*)(u32,u32))0x8007B49Cu)
#define set_order ((void (*)(u32,u32,u32))0x8007B44Cu)
#define choice_window ((void *(*)(void))0x80065040u)
#define choice_index ((int (*)(void *))0x800654FCu)
#define set_choices ((void (*)(void *,const u8 *,int,const u8 *,int,const u8 *,int,const u8 *,int))0x80065278u)
#define name ((int (*)(u8 *,u32,u32))0x801969C8u)
#define msg_window ((void *(*)(void))0x8009D1F0u)
#define continue_msg ((void (*)(void *,u32))0x8009DBA4u)
#define demo_msg ((void (*)(u32))0x8007B5C0u)
#define camera ((void (*)(u32))0x8007BA1Cu)
#define free_count ((int (*)(void *,u32))0x800B8318u)
#define give_item ((int (*)(void *,u32,u32))0x800B8B8Cu)
#define stock_init ((int (*)(Stock *))AF_V3_STOCK_INIT)
#define stock_count ((int (*)(const Stock *,u32))AF_V3_STOCK_COUNT)
#define stock_index ((int (*)(const Stock *,u32,u32))AF_V3_STOCK_INDEX)
#define stock_quote ((int (*)(const Stock *,u32,Offer *))AF_V3_STOCK_QUOTE)
#define stock_commit ((int (*)(Stock *,const Offer *))AF_V3_STOCK_COMMIT)
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#define categories ((const Category *)0x804AEF00u)
#define native_action(i) ((const Action *)(owner+0x1230u))[i]
#define native_info ((void (*)(Vendor *))(owner+0xF38u))
#define money_check ((int (*)(u32))(owner+0x738u))
#define payment ((void (*)(u32))(owner+0x8F0u))
#define price_string ((void (*)(u32,u32))(owner+0x6E4u))
#else
#include "../../tests/v3_event_menu_imports.h"
#endif

void af_v3_event_menu_setup(Vendor *,int);
void af_v3_event_menu_select(Vendor *,void *);
void af_v3_event_menu_purchase(Vendor *,void *);
void af_v3_event_menu_give(Vendor *,void *);
void af_v3_event_menu_route(Vendor *,void *);

static Stock *added(void) {
    Stock *area=get_area(11u,0u);
    return area ? area+1 : 0;
}
static void message(u32 id) { continue_msg(msg_window(),id); }
static int choice_ready(void) {
    if (get_order(4,9)!=1) return 0;
    set_order(4,9,0);
    return 1;
}
static void routes(void) {
    static const u8 original[]="Original wares  ", imported[]="Festival items  ";
    /* Reuse the complete official cancellation label already in the owner. */
    set_choices(choice_window(),original,16,imported,16,owner+0x1250,16,0,16);
}

void af_v3_event_menu_start(Vendor *vendor) {
    if (!vendor || !owner) return;
    vendor->mode=0;
    Stock *stock=added();
    int available=0;
    for (u32 k=0;k<3u;k++) for (u32 i=0;i<8u;i++) {
        int kind=selected(categories[k].first+i);
        available |= kind>=36 && kind<115;
    }
    if (!available || stock_init(stock)!=1 || stock_count(stock,0)<0) {
        native_info(vendor);
        return;
    }
    vendor->mode=2;vendor->next=6;
    routes();demo_msg(AF_V3_EVENT_ROUTE_MESSAGE);camera(9);
}

void af_v3_event_menu_setup(Vendor *vendor,int action) {
    if (!vendor || !owner) return;
    if ((u32)action>6u) action=4;
    Action callback;
    if (action==6) callback=af_v3_event_menu_route;
    else if (vendor->mode==1u && action==1) callback=af_v3_event_menu_select;
    else if (vendor->mode==1u && action==3) callback=af_v3_event_menu_purchase;
    else if (vendor->mode==1u && action==5) callback=af_v3_event_menu_give;
    else callback=native_action(action);
    vendor->action=(u32)action;vendor->proc=(u32)(uptr)callback;
}

void af_v3_event_menu_route(Vendor *vendor,void *game) {
    (void)game;
    if (!choice_ready()) return;
    int choice=choice_index(choice_window());
    if (choice==0) {
        vendor->mode=0;native_info(vendor);
        Stock *stock=get_area(11u,0u);
        int count=0;
        if (stock && stock->kind<3u)
            for (u32 i=0;i<8u;i++) count+=stock->goods[i]!=0;
        message(count ? AF_V3_EVENT_NATIVE_FIRST+stock->kind : 0x1757u);
        af_v3_event_menu_setup(vendor,(int)vendor->next);
    } else if (choice==1) {
        Stock *stock=added();int count=stock_count(stock,0);
        vendor->mode=1;vendor->start=0;
        if (count>0) {
            vendor->price=categories[stock->kind].price;
            message(categories[stock->kind].message);
            af_v3_event_menu_setup(vendor,1);
        } else { message(0x1757);af_v3_event_menu_setup(vendor,4); }
    } else { vendor->mode=0;message(0x175B);af_v3_event_menu_setup(vendor,4); }
}

static int merchandise(Stock *stock,u32 start) {
    u8 names[4][16];const u8 *strings[4]={0,0,0,0};u32 n=0,j=start;
    for (u32 i=0;i<64u;i++) ((u8 *)names)[i]=' ';
    for (;j<8u && n<3u;j++) if (stock->goods[j]) {
        name(names[n],16,stock->goods[j]);strings[n]=names[n];++n;
    }
    strings[n]=owner+(j==8u ? 0x1250u : 0x1260u);
    set_choices(choice_window(),strings[0],16,strings[1],16,strings[2],16,strings[3],16);
    return (int)j;
}

void af_v3_event_menu_select(Vendor *vendor,void *game) {
    (void)game;
    if (!choice_ready()) return;
    Stock *stock=added();int count=stock_count(stock,(u32)vendor->start);
    if (choice_index(choice_window())!=0 || count<=0) {
        af_v3_event_menu_setup(vendor,4);return;
    }
    price_string(vendor->price,0);
    vendor->next_start=(s16)merchandise(stock,(u32)vendor->start);
    message(count<4 ? 0x1761u : 0x1762u);
    af_v3_event_menu_setup(vendor,3);
}

void af_v3_event_menu_purchase(Vendor *vendor,void *game) {
    (void)game;
    if (!choice_ready()) return;
    int choice=choice_index(choice_window());Stock *stock=added();
    int index=stock_index(stock,(u32)vendor->start,(u32)choice);
    af_v3_event_menu_setup(vendor,4);
    if (index<0) {
        if (choice==3 && stock_count(stock,(u32)vendor->start)>=4) {
            vendor->start=vendor->next_start;message(0x1767);
            af_v3_event_menu_setup(vendor,1);
        } else message(0x1763);
        return;
    }
    Offer offer;
    if (!stock_quote(stock,(u32)index,&offer) || offer.price!=vendor->price) {
        message(0x1763);return;
    }
    void *priv=private_data;
    if (!priv || !free_count(priv,0)) { message(0x175D);return; }
    if (!money_check(offer.price)) { message(0x175E);return; }
    if (!give_item(priv,offer.item,0)) { message(0x175D);return; }
    payment(offer.price);
    /* No yield occurs between quotation and commitment. Profile/state remain
       the same while the native inventory/payment routines execute. */
    if (!stock_commit(stock,&offer)) { message(0x1763);return; }
    vendor->item=offer.item;vendor->start=0;
    vendor->next=stock_count(stock,0)==0 ? 4u : 0u;
    af_v3_event_menu_setup(vendor,5);message(0x1764);
}

void af_v3_event_menu_give(Vendor *vendor,void *game) {
    (void)game;
    if (get_order(4,1)!=2) return;
    set_order(5,0,vendor->item);set_order(5,1,7);set_order(5,2,0);
    af_v3_event_menu_setup(vendor,(int)vendor->next);
    /* The original wares remain available even when the added stock sells out.
       Use the official generic farewell instead of claiming the whole shop closes. */
    message(vendor->next==4u ? 0x1760u : 0x1766u);
}
