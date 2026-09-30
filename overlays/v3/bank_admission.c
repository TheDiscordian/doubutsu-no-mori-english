#include "bank_pelly.h"
#include "bank_native.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
int af_bank_native_selected(void) {return af_bank_account_mode==1;}
int af_bank_native_eligible(void) {
    /* The reviewed house arrangement selects the resident's actual home. The
     * highest native floor size is two; the donor's upper-floor size is three.
     * N64 banking uses its completed largest house, not a nonexistent floor. */
    if(af_bank_player>=4 || !af_bank_now_private || ((uptr)af_bank_now_private&3))return 0;
    const u8 *p=af_bank_now_private;
    if((p[0xC]==255 && p[0xD]==255) || (p[0xE]==255 && p[0xF]==255))return 0;
    if((u32)p[0x3C]<<24|(u32)p[0x3D]<<16|(u32)p[0x3E]<<8|p[0x3F])return 0;
    u32 slot=(af_bank_home_arrangement>>(2*af_bank_player))&3;
    const u8 *home=af_bank_native_homes+slot*0xB48u;
    for(u32 i=0;i<16;i++)if(home[i]!=p[i])return 0;
    return home[0x22]>>6==2 && !(home[0x22]&8);
}
