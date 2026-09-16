#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_DISPLAY_ALIASES 1
#include "../overlays/v3/display_items.c"
#include "../overlays/v3/display_conversion.c"
#include "../overlays/v3/display_roster.c"

struct DisplayAliasIndex af_v3_test_alias_index;
unsigned short af_v3_test_alias_items[1024*16];
u8 af_v3_display_profile[192];
static int selected=1;
static u32 last;

int af_v3_item_type(u32 item) { return af_v3_display_item_type(item); }
int af_v3_furniture_import_profile(u32 index) {
    assert(index>=1024 && index<2048);
    if (!selected) return 0;
    u32 item=0x3000+(index-1024)*4;
    const u16 *alias=af_v3_raw_display_alias(item);
    if (!alias) return 0;
    return (alias[0]>>8)!=0x34 || af_v3_all_display_clothing_index(item)!=0;
}
int af_v3_base_item_name(u8 *out,u32 capacity,u32 item) {
    last=item;
    if (!out || capacity<16 || item>65535) return 0;
    memset(out,'X',16);return 1;
}
int af_v3_base_item_type(u32 item) { last=item;return (item>>8)==0x34 ? 12 : 0; }
int af_v3_base_item_place(u32 item,int x,int z,void *out) {
    last=item;assert(x==-4 && z==7 && out);return 0;
}
u32 af_v3_base_item_price(u32 item) { last=item;return item+12; }
void af_v3_prior_catalogue_record(u32 item) { last=item; }
int af_v3_prior_catalogue_owned(const u8 *private,u32 item) { assert(private);last=item;return 1; }
u16 af_v3_prior_display_item(u32 item) { last=item;return (u16)item; }
u16 af_v3_prior_pocket_item(u32 item) { last=item;return (u16)item; }

static void add(u32 parent,u32 display,u32 footprint) {
    u32 i=af_v3_test_alias_index.count++,slot=(display-0x3000)/4;
    af_v3_test_alias_index.rows[i].parent=parent;
    af_v3_test_alias_index.rows[i].display=display;
    u16 *row=af_v3_test_alias_items+slot*16;
    row[0]=1024+slot;row[1]=display;row[14]=parent;row[15]=footprint;
}

int main(void) {
    af_v3_test_alias_index.magic=AF_V3_DISPLAY_ALIAS_MAGIC;
    memset(af_v3_display_profile,255,sizeof af_v3_display_profile);
    /* Synthetic identities deliberately absent from every installed-item list.
     * One uses its own generated footprint, one the garment category. */
    add(0x2200,0x318C,0);add(0x3407,0x381C,0x17AC);
    u8 text[18],private[4]={0};
    for (u32 i=0;i<af_v3_test_alias_index.count;++i) {
        u32 parent=af_v3_test_alias_index.rows[i].parent;
        u32 display=af_v3_test_alias_index.rows[i].display;
        u32 footprint=af_v3_raw_display_alias(display)[1];
        assert(af_v3_room_display_item(parent)==display);
        assert(af_v3_room_display_item(0xABCD0000|parent)==display);
        for (u32 rotation=0;rotation<4;++rotation) {
            u32 item=display|rotation;
            assert(af_v3_room_pocket_item(item)==parent);
            assert(af_v3_room_pocket_item(0xABCD0000|item)==parent);
            assert(af_v3_display_pocket_item(0xABCD0000|item)==(0xABCD0000|item));
            memset(text,0xA5,sizeof text);
            assert(af_v3_display_item_name(text+1,16,item) && last==parent);
            assert(text[0]==0xA5 && text[17]==0xA5);
            assert(!af_v3_display_item_name(text+1,15,item));
            assert(af_v3_display_item_type(item)==10);
            assert(af_v3_display_item_price(item)==parent+12);
            assert(!af_v3_display_item_place(item,-4,7,text));
            assert(last==((footprint ? footprint : display)|rotation));
            af_v3_display_catalogue_record(item);assert(last==parent);
            assert(af_v3_display_catalogue_owned(private,item) && last==parent);
            selected=0;
            assert(af_v3_room_display_item(parent)==parent);
            assert(af_v3_room_pocket_item(item)==item);
            af_v3_display_catalogue_record(item);assert(last==item);
            selected=1;
        }
        u16 *row=af_v3_test_alias_items+(display-0x3000)/4*16;
        row[0]++;
        assert(af_v3_room_display_item(parent)==parent);
        assert(af_v3_room_pocket_item(display)==display);
        row[0]--;
    }
    af_v3_display_profile[96]&=0x7F;
    assert(!af_v3_all_display_clothing_index(0x381C));
    assert(af_v3_room_display_item(0x3407)==0x3407);
    af_v3_display_profile[96]|=0x80;
    assert(af_v3_all_display_clothing_index(0x381F)==0x1007);
    assert(!af_v3_all_display_clothing_index(0x318C));
    assert(af_v3_all_display_clothing_index(0x17B0)==1);
    af_v3_test_alias_index.magic=0;
    assert(af_v3_room_display_item(0x3407)==0x3407);
    af_v3_test_alias_index.magic=AF_V3_DISPLAY_ALIAS_MAGIC;
    af_v3_test_alias_index.count=AF_V3_DISPLAY_ALIAS_CAPACITY+1;
    assert(af_v3_room_display_item(0x3407)==0x3407);
    af_v3_test_alias_index.count=2;
    assert(af_v3_room_display_item(0xABCD2400)==0x2400 && last==0xABCD2400);
    assert(af_v3_display_pocket_item(0xFFFF)==0xFFFF);
    assert(!af_v3_raw_display_alias(0x1000));
    puts("shared display conversion, metadata, category, footprint, ownership, and rejection pass");
}
