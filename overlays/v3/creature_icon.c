/* Both donor palettes remain adjacent: pockets use the first, collection the second. */
typedef unsigned int u32;
extern const u32 af_creature_icons[];
extern int af_creature_item_type(u32);
const u32 *af_v3_creature_icon(u32 item) {
    unsigned index;
    if (item>=0x2320 && item<=0x2328) index=item-0x2320;
    else if (item>=0x2D20 && item<=0x2D27) index=item-0x2D20+9;
    else return 0;
    if (af_creature_item_type(item)!=(index<9 ? 8 : 18) ||
        af_creature_icons[0]!=0x41464350 || af_creature_icons[1]!=1 ||
        af_creature_icons[2]!=17 || af_creature_icons[3]!=8) return 0;
    const u32 *row=af_creature_icons+4+index*2;
    if ((row[0]&31) || (row[1]&31) || row[0]<0x8064A000 || row[0]>0x80654FF0-64 ||
        row[1]<0x8064A000 || row[1]>0x80654FF0-512) return 0;
    return row;
}
