/* Data semantics follow GAFE01 m_needlework.c / m_needlework_ovl.c. Pixel
 * coordinates follow m_design_ovl.c, with the GX tile address replaced by a
 * native row-major address. No native save or menu hooks are installed here. */
#include "carried_designs.h"
typedef __UINTPTR_TYPE__ Address;
static int separate(const void *a,unsigned int an,const void *b,unsigned int bn) {
    Address x=(Address)a,y=(Address)b;
    return x<=y ? an<=y-x : bn<=x-y;
}
static void copy(void *out,const void *in,unsigned int n) {
    unsigned char *d=out;const unsigned char *s=in;
    for(unsigned int i=0;i<n;i++)d[i]=s[i];
}
static int same(const void *a,const void *b,unsigned int n) {
    const unsigned char *x=a,*y=b;
    for(unsigned int i=0;i<n;i++)if(x[i]!=y[i])return 0;
    return 1;
}
static int valid_record(const AFDesign *d) {
    if(!d || d->palette>=AF_DESIGN_PALETTES || d->flags>1)return 0;
    for(unsigned int i=0;i<sizeof(d->reserved);i++)if(d->reserved[i])return 0;
    return 1;
}
__attribute__((section(".text.entry")))
int af_design_valid(const AFDesigns *s) {
    if(!s)return 0;
    for(unsigned int p=0;p<AF_DESIGN_PLAYERS;p++) {
        unsigned int used=0;
        for(unsigned int i=0;i<AF_DESIGN_SLOTS;i++) {
            unsigned int index=s->order[p][i];
            if(index>=AF_DESIGN_SLOTS || used&(1u<<index) || !valid_record(&s->patterns[p][i]))return 0;
            used|=1u<<index;
        }
    }
    return 1;
}
int af_design_reset_player(AFDesigns *s,unsigned int player,const AFDesign templates[8]) {
    if(!s || !templates || player>=AF_DESIGN_PLAYERS ||
            !separate(s,sizeof(*s),templates,AF_DESIGN_SLOTS*sizeof(*templates)))return AF_DESIGN_ARGUMENT;
    for(unsigned int i=0;i<AF_DESIGN_SLOTS;i++)if(!valid_record(templates+i))return AF_DESIGN_ARGUMENT;
    copy(s->patterns[player],templates,AF_DESIGN_SLOTS*sizeof(*templates));
    for(unsigned int i=0;i<AF_DESIGN_SLOTS;i++)s->order[player][i]=i;
    return AF_DESIGN_OK;
}
int af_design_reset(AFDesigns *s,const AFDesign templates[8]) {
    /* Validate the whole input before changing even the first player. */
    if(!s || !templates || !separate(s,sizeof(*s),templates,8*sizeof(*templates)))return AF_DESIGN_ARGUMENT;
    for(unsigned int i=0;i<8;i++)if(!valid_record(templates+i))return AF_DESIGN_ARGUMENT;
    for(unsigned int p=0;p<AF_DESIGN_PLAYERS;p++)af_design_reset_player(s,p,templates);
    return AF_DESIGN_OK;
}
const AFDesign *af_design_physical(const AFDesigns *s,unsigned int p,unsigned int i) {
    if(!s || p>=AF_DESIGN_PLAYERS || i>=AF_DESIGN_SLOTS || !valid_record(&s->patterns[p][i]))return 0;
    return &s->patterns[p][i];
}
const AFDesign *af_design_selected(const AFDesigns *s,unsigned int p,unsigned int slot) {
    if(!s || p>=AF_DESIGN_PLAYERS || slot>=AF_DESIGN_SLOTS)return 0;
    return af_design_physical(s,p,s->order[p][slot]);
}
int af_design_reorder(AFDesigns *s,unsigned int p,unsigned int a,unsigned int b) {
    if(p>=AF_DESIGN_PLAYERS || a>=AF_DESIGN_SLOTS || b>=AF_DESIGN_SLOTS || !af_design_valid(s))return AF_DESIGN_ARGUMENT;
    if(a==b)return AF_DESIGN_UNCHANGED;
    unsigned char old=s->order[p][a];s->order[p][a]=s->order[p][b];s->order[p][b]=old;
    return AF_DESIGN_OK;
}
int af_design_begin(AFDesignDraft *d,const AFDesigns *s,unsigned int p,unsigned int slot) {
    const AFDesign *original=af_design_selected(s,p,slot);
    if(!d || !original || !af_design_valid(s) || !separate(d,sizeof(*d),s,sizeof(*s)))return AF_DESIGN_ARGUMENT;
    d->player=p;d->index=s->order[p][slot];
    copy(&d->original,original,sizeof(*original));copy(&d->edited,original,sizeof(*original));
    return AF_DESIGN_OK;
}
int af_design_pixel(const AFDesign *d,int x,int y) {
    if(!d || (unsigned int)x>=32 || (unsigned int)y>=32)return AF_DESIGN_ARGUMENT;
    unsigned int i=(unsigned int)y*16+(unsigned int)x/2;
    return d->texture[i]>>((x&1)?0:4)&15;
}
int af_design_paint(AFDesign *d,int x,int y,unsigned int colour) {
    int old=af_design_pixel(d,x,y);
    if(old<0 || colour>=16)return AF_DESIGN_ARGUMENT;
    if((unsigned int)old==colour)return AF_DESIGN_UNCHANGED;
    unsigned int i=(unsigned int)y*16+(unsigned int)x/2,shift=(x&1)?0:4;
    d->texture[i]=(d->texture[i]&~(15u<<shift))|(colour<<shift);
    return AF_DESIGN_OK;
}
int af_design_fill(AFDesign *d,int x,int y,unsigned int colour,AFDesignFillWork *work) {
    int old=af_design_pixel(d,x,y);
    if(old<0 || colour>=16 || !work || !separate(d,sizeof(*d),work,sizeof(*work)))return AF_DESIGN_ARGUMENT;
    if((unsigned int)old==colour)return AF_DESIGN_UNCHANGED;
    unsigned int head=0,tail=1;work->queue[0]=y*32+x;
    af_design_paint(d,x,y,colour);
    while(head<tail) {
        unsigned int at=work->queue[head++];int px=at%32,py=at/32;
        const int dx[4]={-1,1,0,0},dy[4]={0,0,-1,1};
        for(unsigned int i=0;i<4;i++) {
            int xx=px+dx[i],yy=py+dy[i];
            if(af_design_pixel(d,xx,yy)==old) {
                /* Mark before enqueueing: every pixel can enter only once,
                 * so the bounded 1024-entry queue cannot overflow. */
                af_design_paint(d,xx,yy,colour);work->queue[tail++]=yy*32+xx;
            }
        }
    }
    return AF_DESIGN_OK;
}
int af_design_palette(AFDesign *d,unsigned int palette) {
    if(!d || palette>=AF_DESIGN_PALETTES)return AF_DESIGN_ARGUMENT;
    if(d->palette==palette)return AF_DESIGN_UNCHANGED;
    d->palette=palette;return AF_DESIGN_OK;
}
int af_design_name(AFDesign *d,const unsigned char *name,unsigned int length) {
    if(!d || !name || !length || length>16)return AF_DESIGN_ARGUMENT;
    /* Names are fixed-width glyph fields, never executable text commands. */
    for(unsigned int i=0;i<length;i++)if(name[i]==0x7F || name[i]==0x80)return AF_DESIGN_ARGUMENT;
    unsigned char result[16];
    for(unsigned int i=0;i<16;i++)result[i]=i<length?name[i]:' ';
    if(same(result,d->name,16))return AF_DESIGN_UNCHANGED;
    copy(d->name,result,16);return AF_DESIGN_OK;
}
int af_design_commit(AFDesigns *s,const AFDesignDraft *d,AFDesigns *scratch,AFDesignCapacity capacity,void *context) {
    if(!s || !d || !scratch || !capacity || !af_design_valid(s) ||
            d->player>=4 || d->index>=8 || !valid_record(&d->edited) || !valid_record(&d->original) ||
            !separate(s,sizeof(*s),scratch,sizeof(*scratch)) ||
            !separate(s,sizeof(*s),d,sizeof(*d)) || !separate(scratch,sizeof(*scratch),d,sizeof(*d)))
        return AF_DESIGN_ARGUMENT;
    AFDesign *current=&s->patterns[d->player][d->index];
    if(!same(current,&d->original,sizeof(*current)))return AF_DESIGN_CHANGED;
    if(same(current,&d->edited,sizeof(*current)))return AF_DESIGN_UNCHANGED;
    copy(scratch,s,sizeof(*s));copy(&scratch->patterns[d->player][d->index],&d->edited,sizeof(*current));
    if(capacity(context,scratch)<=0)return AF_DESIGN_CAPACITY;
    copy(current,&d->edited,sizeof(*current));return AF_DESIGN_OK;
}
