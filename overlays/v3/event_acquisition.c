/* Added event stock is separate from original N64 merchandise. These helpers
   never grant an item or debit Bells: the menu transaction commits first. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 first, price, message; u8 count, kind; } Category;
typedef struct { u16 goods[8], count, kind; } Stock;
typedef struct { u16 item, price, message, slot; } Offer;
_Static_assert(sizeof(Category)==8, "Event category stride");
_Static_assert(sizeof(Stock)==20, "Event stock fits the unused native tail");
#ifdef __mips__
#define categories ((const Category *)0x804AEF00u)
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#define random_float ((float (*)(void))0x8002C9ACu)
#define get_area ((u8 *(*)(u32,u32))0x8008033Cu)
#define owner (*(u8 **)0x80101BC0u)
#else
extern Category af_test_event_categories[3];
extern int af_test_event_selected(u32);
extern float af_test_event_random(void);
extern u8 *af_test_event_get_area(u32,u32), *af_test_event_owner;
extern void af_test_event_original(void);
#define categories af_test_event_categories
#define selected af_test_event_selected
#define random_float af_test_event_random
#define get_area af_test_event_get_area
#define owner af_test_event_owner
#endif

static int configuration(void) {
    for (u32 i=0;i<3u;i++) {
        const Category *row=categories+i;
        if (row->kind!=i || row->count!=8u || row->first<0x2224u ||
            row->first>0x2254u || !row->price || !row->message) return 0;
        for (u32 j=0;j<i;j++)
            if (row->first<categories[j].first+8u && categories[j].first<row->first+8u) return 0;
    }
    return 1;
}

static int allowed(u32 item) {
    int kind=selected(item);
    return kind>=36 && kind<115;
}

static int valid(const Stock *stock) {
    if (!stock || !configuration() || stock->count!=8u || stock->kind>=3u) return 0;
    const Category *row=categories+stock->kind;
    for (u32 i=0;i<8u;i++)
        if (stock->goods[i] && (stock->goods[i]!=row->first+i || !allowed(stock->goods[i]))) return 0;
    return 1;
}

/* A zero tail means uninitialised, not sold out. Keep eight stable slots and
   the donor's count marker even with sparse selections or after every sale. */
int af_v3_event_stock_init(Stock *stock) {
    if (!stock || !configuration()) return -1;
    if (stock->count) return valid(stock) ? 1 : -1;
    if (stock->kind) return -1;
    for (u32 i=0;i<8u;i++) if (stock->goods[i]) return -1;
    u8 masks[3]={0,0,0}, available[3];
    u32 count=0;
    for (u32 kind=0;kind<3u;kind++) {
        for (u32 i=0;i<8u;i++)
            if (allowed(categories[kind].first+i)) masks[kind]|=(u8)(1u<<i);
        if (masks[kind]) available[count++]=(u8)kind;
    }
    if (!count) return 0; /* Disabled imports consume no RNG and write nothing. */
    float draw=random_float();
    if (!(draw>=0.0f && draw<1.0f)) return -1;
    u32 kind=available[(u32)(draw*(float)count)];
    for (u32 i=0;i<8u;i++)
        stock->goods[i]=(masks[kind]&(1u<<i)) ? (u16)(categories[kind].first+i) : 0;
    stock->kind=(u16)kind;
    stock->count=8;
    return 1;
}

int af_v3_event_stock_count(const Stock *stock, u32 start) {
    if (start>8u || !valid(stock)) return -1;
    int count=0;
    for (u32 i=start;i<8u;i++) count+=stock->goods[i]!=0;
    return count;
}

/* Three merchandise choices, with index three reserved for next/cancel, as
   in the donor. Return the actual slot, never a compacted saved identity. */
int af_v3_event_stock_index(const Stock *stock, u32 start, u32 choice) {
    if (start>=8u || choice>=3u || !valid(stock)) return -1;
    for (u32 i=start;i<8u;i++) if (stock->goods[i]) {
        if (!choice) return (int)i;
        --choice;
    }
    return -1;
}

int af_v3_event_stock_quote(const Stock *stock, u32 slot, Offer *offer) {
    if (!offer || slot>=8u || !valid(stock) || !stock->goods[slot]) return 0;
    *offer=(Offer){stock->goods[slot],categories[stock->kind].price,
        categories[stock->kind].message,(u16)slot};
    return 1;
}

/* Call only after pocket insertion and payment succeed. Checking the quoted
   identity and price prevents a stale menu selection from consuming another row. */
int af_v3_event_stock_commit(Stock *stock, const Offer *offer) {
    Offer actual;
    if (!offer || !af_v3_event_stock_quote(stock,offer->slot,&actual) ||
        actual.item!=offer->item || actual.price!=offer->price || actual.message!=offer->message) return 0;
    stock->goods[offer->slot]=0;
    return 1;
}

void af_v3_event_stock_construct(void) {
    u8 *loaded=owner;
    if (!loaded) return;
#ifdef __mips__
    ((void (*)(void))(loaded+0x4B8u))(); /* Existing allocation/stock routine. */
#else
    af_test_event_original();
#endif
    u8 *area=get_area(11u,0u);
    if (area) af_v3_event_stock_init((Stock *)(area+20u));
}
