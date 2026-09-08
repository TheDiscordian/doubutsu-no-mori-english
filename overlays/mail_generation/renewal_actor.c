#include "renewal_actor.h"

typedef struct {
    AfLeafletWork generation;
    unsigned char mail[164];
} RenewalWork;

#ifdef __mips__
typedef char renewal_work_size[sizeof(RenewalWork) == 5456 ? 1 : -1];
static int heap_range(void *allocation,unsigned int size) {
    unsigned int address = (unsigned int)allocation;
    return address >= 0x8019C8E0u && address <= 0x80400000u-size;
}
#else
extern int af_renewal_test_heap_range(void *,unsigned int);
#define heap_range af_renewal_test_heap_range
#endif

int af_renewal_deliver(unsigned int shop_level,const unsigned char *reopening_time) {
    unsigned char slots[4],players[4];
    unsigned int home,mask = 0,capital,size;
    int slot,result = 0;
    AfLeafletChoice choice;
    void *allocation;
    RenewalWork *work;
    if (!reopening_time || af_mail_generation_capital > 1u) return 0;
    for (home = 0; home < 4u; ++home) {
        unsigned int offset = home*0xB48u;
        players[home] = (unsigned char)(af_renewal_house_player(home)&3);
        slot = af_renewal_free_mail(af_renewal_save+0x3A00u+offset,10u);
        if (slot < 0 || (af_renewal_save[0x3596u+offset] == 255u
                        && af_renewal_save[0x3597u+offset] == 255u)
                || af_renewal_working_player(players[home])) continue;
        if (slot >= 10) return 0;
        slots[home] = (unsigned char)slot;
        mask |= 1u << home;
    }
    if (!mask) return 1;
    shop_level &= 3u;
    choice.template_id = (unsigned short)(24u+(shop_level < 2u ? shop_level : 2u));
    choice.year = (unsigned short)(((unsigned int)reopening_time[6]<<8)|reopening_time[7]);
    choice.month = reopening_time[5]; choice.day = reopening_time[3]; choice.hour = reopening_time[2];
    choice.item_count = 0;
    for (home = 0; home < 3u; ++home) choice.items[home] = 0;
    size = sizeof(RenewalWork)+15u;
    allocation = af_renewal_malloc(size);
    if (!allocation) return 0;
    if (!heap_range(allocation,size)) goto done;
    work = (RenewalWork *)(((__UINTPTR_TYPE__)allocation+15u)&~(__UINTPTR_TYPE__)15u);
    af_renewal_clear_mail(work->mail);
    capital = af_mail_generation_capital;
    if (!af_leaflet_create(work->mail,164u,&choice,0,&capital,&work->generation)) goto done;
    /* There are no more fallible generation operations after the first copy.
     * The native main game thread owns these arrays throughout this call.
     */
    for (home = 0; home < 4u; ++home) if (mask & (1u << home)) {
        af_renewal_copy_id(work->mail,af_renewal_save+0x20u+players[home]*0xBD0u);
        work->mail[0x10] = 0;
        af_renewal_copy_mail(af_renewal_save+0x3A00u+home*0xB48u+slots[home]*164u,work->mail);
    }
    af_mail_generation_capital = capital;
    result = 1;
done:
    af_renewal_free(allocation);
    return result;
}
