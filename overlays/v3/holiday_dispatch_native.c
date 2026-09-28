/* Identities become available only with their real installed providers. */
#include "holiday_dispatch.h"
#include "npc_registry.h"
extern const unsigned char af_holiday_transition_maps[1496];
extern int af_holiday_transition_live_fade(void *,void *,unsigned int,unsigned int,
    unsigned int,unsigned int);
/* Fixed o32 decoration directory, shared with decoration_actor.h. Read the
 * identity/dependency prefix without importing its source-adaptation macros. */
typedef struct {
    unsigned short source,name,profile,owner,source_dummy,native_dummy;
    unsigned int dependencies;
    void (*callbacks[4])(void *,void *);
} Decoration;
extern const Decoration af_decor_actor_records[18];
extern const unsigned int af_holiday_decoration_ready;
#ifdef __mips__
_Static_assert(sizeof(Decoration)==32,"Installed decoration record stride");
#endif
static int resolve(void *context,unsigned int kind,unsigned int source) {
    (void)context;
    if(kind!=AF_HD_NAME || source>65535)return -1;
    for(unsigned int i=0;i<18;i++) {
        const Decoration *r=&af_decor_actor_records[i];
        if(r->source==source && r->name &&
           (r->dependencies&af_holiday_decoration_ready)==r->dependencies)return r->name;
    }
    unsigned int name=source==0xD074?0xD090:source==0xD03D?0xD091:0;
    const AFNpcExtras *t=&af_v3_npc_extras;
    if(!name || t->magic!=AF_NPC_EXTRA_MAGIC || t->version!=1 ||
       t->stride!=44 || t->count>AF_NPC_EXTRA_MAX)return -1;
    for(unsigned int i=0;i<t->count;i++)
        if(t->rows[i].name==name && t->rows[i].flags==3)return name;
    /* No same-number fallback for participants, controllers, or effects.
     * Their event storage/lifecycle must be connected before admission. */
    return -1;
}
int af_holiday_dedicated_bind(AFHolidayDedicatedServices *s) {
    if(!s)return 0;
    *s=(AFHolidayDedicatedServices){.resolve=resolve,.fade=af_holiday_transition_live_fade,
        .maps=af_holiday_transition_maps,.map_bytes=1496};
    return 1;
}
