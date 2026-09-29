/* Source weed thresholds count all saved town acres at spawn and the current
 * field at reward selection. Neither query alters scenery or saved data. */
#include "carried_event.h"
extern const u16 af_cw_native_foreground[6][5][256];
extern int af_cw_native_field_ready(void);
extern u8 af_cw_native_field_width(void),af_cw_native_field_height(void);
extern const u16 *af_cw_native_acre(int,int);
extern u8 af_cw_native_homes[4][0xB48];
static int count(const u16 *items,u16 first,u16 last) {
    int result=0;
    if(items)for(unsigned i=0;i<256;i++)result+=items[i]>=first && items[i]<=last;
    return result;
}
int mFI_GetItemNumField_BCT(u16 first,u16 last) {
    if(first!=8 || last!=10)return 0;
    int result=0;
    for(unsigned z=0;z<6;z++)for(unsigned x=0;x<5;x++)
        result+=count(af_cw_native_foreground[z][x],first,last);
    return result;
}
int mFI_GetItemNumField(u16 first,u16 last) {
    if(first!=8 || last!=10 || !af_cw_native_field_ready())return 0;
    unsigned width=af_cw_native_field_width(),height=af_cw_native_field_height();
    if(width>7 || height>8)return 0;
    int result=0;
    for(unsigned z=0;z<height;z++)for(unsigned x=0;x<width;x++)
        result+=count(af_cw_native_acre((int)x,(int)z),first,last);
    return result;
}
void af_cw_set_roof(int index,unsigned colour) {
    int player=af_cw_player();
    if(player<0 || player>=4 || !af_cw_private() || index<0 || index>=4 ||
       colour>=12 || mHS_get_arrange_idx(player)!=index)return;
    /* Native 24 is the current roof; 25 is an ordered house-upgrade colour.
     * The source's separate next-paint field has no native counterpart. Apply
     * this immediate reward without changing the existing upgrade order. */
    af_cw_native_homes[index][0x24]=(u8)colour;
}
