/* Shared ground/handover category identities. Native types keep their values;
   imported types use native-count + donor-type, independently of selections. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 item, price, display; u8 kind, source_type; u8 name[16]; } Parent;
_Static_assert(sizeof(Parent)==24, "Equipment parent stride");
#ifdef __mips__
#ifndef AF_V3_CATEGORY_ORIGINAL
#define AF_V3_CATEGORY_ORIGINAL 0x800A5630u
#endif
#define parents ((const u32 *)0x804A87F0u)
#define categories ((const u32 *)0x804AA200u)
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#define original ((int (*)(u32))AF_V3_CATEGORY_ORIGINAL)
#else
extern u32 af_test_category_parents[340], af_test_categories[32];
extern int af_test_category_selected(u32), af_test_category_original(u32);
#define parents af_test_category_parents
#define categories af_test_categories
#define selected af_test_category_selected
#define original af_test_category_original
#endif

int af_v3_equipment_category(u32 argument) {
    u32 item=(u16)argument, index=item-0x2224u;
    if (index>=56u) return original(argument);
    /* Never let a missing/disabled extended identity index the native short
       equipment table. The shared selector includes actual profile readiness. */
    if (parents[0]!=0x41464849u || parents[1]!=1u || parents[2]!=56u || parents[3]!=24u ||
        categories[0]!=0x41464354u || categories[1]!=1u ||
        categories[2]!=AF_V3_CATEGORY_COUNT || categories[3]!=53u) return 0;
    const Parent *row=(const Parent *)(parents+4)+index;
    if (row->item!=item || row->kind<36u || row->kind>=115u || row->source_type>=53u ||
        row->display<0x3000u || row->display>=0x4000u || (row->display&3u) ||
        selected(item)!=(int)row->kind) return 0;
    u32 type=((const u8 *)(categories+4))[row->source_type];
    return type==27u+row->source_type && type<AF_V3_CATEGORY_COUNT ? (int)type : 0;
}
