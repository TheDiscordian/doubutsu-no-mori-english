/* Additive stationery uses the full resident artwork and independent saved
 * ownership. Original catalogue pages retain their complete native paths. */
#include "carried_items.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int (*NativeBit)(const u32 *,int);
typedef struct {
    u16 style;u8 padding[0x742];u32 buffer,profile,segment_offset;
    u16 type,timer;u32 price;float scale,height;
} PaperPreview;
_Static_assert(sizeof(PaperPreview)==0x760,"Native complete preview width");
_Static_assert(__builtin_offsetof(PaperPreview,buffer)==0x744,"Native paper buffer");
extern int af_carried_prior_catalogue_bit(const u32 *,int,NativeBit);
extern int af_carried_owned(const u8 *,u32);
extern u32 af_carried_price(u32);
#ifdef __mips__
#define active (*(u8 *volatile *)0x80136FD8u)
static void original(PaperPreview *p,u32 item) {
    u8 *menu=*(u8 *volatile *)0x8010DCECu;
    u32 init=*(volatile u32 *)(menu+0x2CA0);
    ((void (*)(PaperPreview *,u32))(init+0x808A6730u-0x808A96ACu))(p,item);
}
#else
extern u8 *af_test_carried_active;
#define active af_test_carried_active
extern void af_test_carried_paper_init(PaperPreview *,u32);
#define original af_test_carried_paper_init
#endif
int af_carried_catalogue_bit(const u32 *bits,int index,NativeBit native) {
    if(active && (const u8 *)bits==active+0xB78 && (u32)index>=64u) {
        /* Catalogue offers one four-sheet pack. Other quantities share the
         * collection identity but are not duplicate catalogue entries. */
        return index==67 && af_carried_owned(active,0x2043u);
    }
    return af_carried_prior_catalogue_bit(bits,index,native);
}
void af_carried_paper_init(PaperPreview *p,u32 argument) {
    u32 item=(u16)argument;
    if(item-0x2040u>=4u) {original(p,argument);return;}
    if(!p)return;
    p->price=0;p->profile=0;p->segment_offset=0;p->type=5;
    if(af_carried_category(item)!=49)return;
    p->style=64;p->height=-93.0f;p->scale=0.28f;p->type=1;
    p->price=af_carried_price(item);
}
