/* One native inventory policy for all exercise cards and Harvest cutlery.
 * Keep original item/menu handlers for every other identity. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define WORD(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(u16 *)((u8 *)(p)+(o)))
#ifdef __mips__
#define PTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define ACTIVE (*(u8 **)0x80136FD8u)
static void *native(u32 at) {
    if(at>=0x8086F310u) at=WORD(*(void **)0x8010DCECu,0x2CC0)-0x808787A0u+at;
    return (void *)at;
}
#else
extern void *af_test_event_item_pointer(void *,u32),*af_test_event_item_function(u32);
extern u8 *af_test_event_item_active;
#define PTR af_test_event_item_pointer
#define ACTIVE af_test_event_item_active
#define native af_test_event_item_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_hi_prior_menu(void *,u32,int);
extern u16 af_holiday_item_display(u32);
static int event_item(u32 item) {return item-0x2523u<14u;}
static int ordinary_slot(int slot) {
    return ACTIVE && (unsigned)slot<15u && !(WORD(ACTIVE,0x34)>>(slot*2)&3u);
}
static void *component(void *submenu,u32 at) {
    void *overlay=submenu?PTR(submenu,0x2C):0;
    return overlay?PTR(overlay,at):0;
}

int af_hi_menu_type(void *submenu,u32 item,int slot) {
    if(event_item(item) && ordinary_slot(slot) && af_holiday_item_display(item)==item)
        return AF_HI_MENU;
    return af_hi_prior_menu(submenu,item,slot);
}

/* These replace table entries, not the predecessor functions. Existing fish,
 * gift, and furniture behaviour therefore stays in the original call chain. */
#define FILTER(name) \
    extern int af_hi_prior_##name(int,int); \
    int af_hi_filter_##name(int slot,int argument) { \
        if(!ACTIVE || (unsigned)slot>=15u || event_item(HALF(ACTIVE,0x14+slot*2)))return 0; \
        return af_hi_prior_##name(slot,argument); \
    }
FILTER(entrust)
FILTER(sell)
FILTER(give)
FILTER(take)
FILTER(furniture)
FILTER(exchange)
int af_hi_filter_unrestricted(int slot,int argument) {
    (void)argument;
    return ACTIVE && (unsigned)slot<15u && !event_item(HALF(ACTIVE,0x14+slot*2));
}

int af_hi_mail_allowed(u32 item,int condition) {
    if(event_item(item))return 0;
    return FN(0x80870AC4u,int,u32,int)(item,condition);
}
void af_hi_mail_warning(void *submenu,void *menu,int warning) {
    void *hand=component(submenu,0x106D4);
    u32 item=hand?HALF(hand,0x23C):0;
    if(event_item(item))warning=item==0x2530u?AF_HI_WARNING+1:AF_HI_WARNING;
    FN(0x80871570u,void,void *,void *,int)(submenu,menu,warning);
}

void af_hi_confirm(void *submenu,void *menu) {
    u8 *owner=component(submenu,0x106D0);
    if(!owner || !menu || WORD(owner,0)>=4u)return;
    u8 *tag=owner+8+WORD(owner,0)*84u;
    if(tag[0]!=AF_HI_MENU)return;
    FN(0x80870A1Cu,void,void *,void *,void *,int)(submenu,menu,tag,AF_HI_CONFIRM);
    FN(0x800D1A9Cu,void,int)(0x33);
}
void af_hi_discard(void *submenu,void *menu) {
    (void)menu;
    u8 *owner=component(submenu,0x106D0),*inventory=component(submenu,0x106DC);
    if(!owner || !inventory)return;
    int slot=FN(0x8086F910u,int,void *)(owner+8);
    if(!ordinary_slot(slot) || WORD(owner+8,0x34)!=0 ||
            !event_item(HALF(ACTIVE,0x14+slot*2)) || HALF(inventory,0x3F4))return;
    /* Donor 12 ticks at 60 Hz -> native six ticks and its 1/6 shrink renderer. */
    HALF(inventory,0x3F4)=6;inventory[0x3DF+slot]=1;
    FN(0x8086F4ACu,int,void *,int,int)(submenu,0,0);
    FN(0x800D1A9Cu,void,int)(0x435);
}
void af_hi_delete_tick(void *submenu,void *tag) {
    u8 *inventory=component(submenu,0x106DC);
    if(tag && inventory && WORD(tag,0x34)==0) {
        int slot=FN(0x8086F910u,int,void *)(tag);
        if(ordinary_slot(slot) && event_item(HALF(ACTIVE,0x14+slot*2)) &&
                inventory[0x3DF+slot]==1 && HALF(inventory,0x3F4)) {
            if(--HALF(inventory,0x3F4)==0) {
                FN(0x800B8B08u,void,void *,int,u32,int)(ACTIVE,slot,0,0);
                inventory[0x3DF+slot]=0;
                FN(0x8086FD3Cu,void,void *)(submenu);
            }
            return;
        }
    }
    FN(0x80876B18u,void,void *,void *)(submenu,tag);
}
