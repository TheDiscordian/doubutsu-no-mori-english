#include "event_leaflet.h"
#include "../../runtime/item_name.h"

#ifdef __mips__
typedef char event_leaflet_work_size[sizeof(AfEventLeafletWork) == 5536 ? 1 : -1];
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    return x <= y ? y-x < as : x-y < bs;
}

int af_event_leaflet_publish(const unsigned char *event, unsigned int event_bytes,
    unsigned int template_id, unsigned int item_count, unsigned int *capital,
    AfEventLeafletWork *work) {
    unsigned int sale, time, i, state;
    if (!event || event_bytes != 156u || !capital || ((__UINTPTR_TYPE__)capital & 3u)
            || !work || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(event,event_bytes,work,sizeof(*work))
            || overlap(event,event_bytes,capital,sizeof(*capital))
            || overlap(work,sizeof(*work),capital,sizeof(*capital)) || *capital > 1u) return 0;
    sale = template_id >= 2u && template_id <= 17u;
    if ((!sale && !(template_id >= 49u && template_id <= 51u))
            || (sale ? !item_count || item_count > 3u
                       || item_count > 1u+(template_id-2u)/4u : item_count)) return 0;
    time = sale ? 12u : 0u;
    work->choice.template_id = (unsigned short)template_id;
    work->choice.year = (unsigned short)(((unsigned int)event[time+6u]<<8)|event[time+7u]);
    work->choice.month = event[time+5u];
    work->choice.day = event[time+3u];
    work->choice.hour = event[time+2u];
    work->choice.item_count = (unsigned char)item_count;
    for (i = 0; i < 3u; ++i) {
        work->choice.items[i] = 0;
        if (i < item_count) {
            unsigned int item = ((unsigned int)event[28u+i*2u]<<8)|event[29u+i*2u];
            if (!item || !af_load_item_name(work->items[i].name.text,16u,item)) return 0;
            work->choice.items[i] = work->items[i].item = (unsigned short)item;
            work->items[i].name.length = 16u;
            /* The supplied GC shop setter uses Set_free_str, not the _art
             * variant: no article is inferred from a name or item identity.
             */
            work->items[i].name.article = 0;
        }
    }
    af_event_leaflet_clear_mail(work->mail);
    state = *capital;
    if (!af_leaflet_create(work->mail,164u,&work->choice,sale ? work->items : 0,
                          &state,&work->generation)) return 0;
    /* Guarded native mode two copies the entire mail to the saved event slot,
     * clears its two receipt flags, and returns one. It has no queue/allocation
     * failure after writing. No native handbill field table is used or changed.
     */
    if (af_event_leaflet_receipt(work->mail,2u) != 1) return 0;
    *capital = state;
    return 1;
}
