#include "leaflet.h"
#include "../../runtime/dateformat.h"

int af_leaflet_hour(unsigned char *, unsigned int);

#ifdef __mips__
typedef char leaflet_choice_size[sizeof(AfLeafletChoice) == 14 ? 1 : -1];
typedef char leaflet_item_size[sizeof(AfLeafletItem) == 20 ? 1 : -1];
typedef char leaflet_work_size[sizeof(AfLeafletWork) == 5280 ? 1 : -1];
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    return a && b && as && bs && (x <= y ? y-x < as : x-y < bs);
}

static unsigned int month_days(unsigned int year, unsigned int month) {
    if (month == 2u)
        return 28u + (!(year % 4u) && (year % 100u || !(year % 400u)));
    return month == 4u || month == 6u || month == 9u || month == 11u ? 30u : 31u;
}

int af_leaflet_create(unsigned char *mail, unsigned int size,
    const AfLeafletChoice *choice, const AfLeafletItem *items,
    unsigned int *capital, AfLeafletWork *work) {
    unsigned int id, year, month, day, count, item_bytes, sale, renewal, i, slot;
    unsigned char text[16];
    int length;
    if (!mail || size != 164u || !choice || ((__UINTPTR_TYPE__)choice & 1u)
            || !capital || ((__UINTPTR_TYPE__)capital & 3u) || !work
            || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(work,sizeof(*work),mail,size)
            || overlap(work,sizeof(*work),choice,sizeof(*choice))
            || overlap(work,sizeof(*work),capital,sizeof(*capital))
            || overlap(mail,size,choice,sizeof(*choice))
            || overlap(mail,size,capital,sizeof(*capital))
            || overlap(capital,sizeof(*capital),choice,sizeof(*choice))) return 0;
    id = choice->template_id; year = choice->year; month = choice->month;
    day = choice->day; count = choice->item_count;
    sale = id >= 2u && id <= 17u;
    renewal = id >= 24u && id <= 26u;
    if ((!sale && !renewal && !(id >= 49u && id <= 51u))
            || year < 1901u || year > 2099u || month < 1u || month > 12u
            || !day || day > month_days(year,month) || choice->hour >= 24u
            || *capital > 1u || count > 3u
            || (sale ? !count || !items || count > 1u+(id-2u)/4u : count || items)
            || ((__UINTPTR_TYPE__)items & 1u)) return 0;
    item_bytes = count*sizeof(*items);
    if (overlap(work,sizeof(*work),items,item_bytes)
            || overlap(mail,size,items,item_bytes)
            || overlap(capital,sizeof(*capital),items,item_bytes)) return 0;
    for (i = 0; i < 3u; ++i) {
        if (i < count) {
            if (!choice->items[i] || items[i].item != choice->items[i]
                    || items[i].name.length != 16u || items[i].name.article > 4u) return 0;
        } else if (choice->items[i]) return 0;
    }
    if (renewal) {
        if (day > 1u) --day;
        else {
            if (month > 1u) --month;
            else { month = 12u; if (--year < 1901u) return 0; }
            day = month_days(year,month);
        }
    }
    af_mail_capture_reset(&work->capture);
    work->capture.capital = *capital;
    slot = sale ? 17u : 0u;
    if (af_format_month(text,month) < 1
            || !af_mail_capture_set(&work->capture,slot,text,9u,0u)
            || af_format_day(text,day) < 1
            || !af_mail_capture_set(&work->capture,slot+1u,text,4u,0u)) return 0;
    length = renewal ? af_format_year(text,year) : af_leaflet_hour(text,choice->hour);
    if (length < 1 || !af_mail_capture_set(&work->capture,slot+2u,text,(unsigned int)length,0u)) return 0;
    if (sale) {
        text[0] = (unsigned char)('0'+count);
        if (!af_mail_capture_set(&work->capture,0u,text,1u,0u)) return 0;
        for (i = 0; i < count; ++i)
            if (!af_mail_capture_set(&work->capture,7u+i,items[i].name.text,
                    items[i].name.length,items[i].name.article)) return 0;
    }
    for (i = 0; i < sizeof(work->selection); ++i)
        ((unsigned char *)&work->selection)[i] = 0;
    work->selection.catalog = AF_MAIL_CATALOG_ID;
    work->selection.templates[0] = (unsigned short)id;
    for (i = 0; i < size; ++i) work->mail[i] = mail[i];
    if (!af_mail_generate(work->mail,size,&work->capture,&work->selection,&work->generation)) return 0;
    work->mail[0x26] = 0u;
    work->mail[0x28] = sale || renewal ? 2u : 3u;
    work->mail[0x29] = sale || renewal ? 55u : 54u;
    for (i = 0; i < size; ++i) mail[i] = work->mail[i];
    *capital = work->capture.capital;
    return 1;
}
