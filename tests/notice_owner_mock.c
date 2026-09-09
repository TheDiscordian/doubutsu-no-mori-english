#include <string.h>
typedef void (*Deposit)(unsigned char *, unsigned int, unsigned int, unsigned int,
                        unsigned char *, unsigned int, void *);
unsigned char af_notice_owner_foreground[15360], af_notice_owner_buried[960];
unsigned char af_notice_owner_timestamp[8], af_notice_owner_board[1560];
unsigned int af_notice_owner_acre, af_notice_owner_unit, af_notice_owner_hole;
unsigned int af_notice_owner_mode, af_notice_owner_place_calls, af_notice_owner_deposit_calls;
unsigned int af_notice_owner_post_calls, af_notice_owner_rtc_calls;
static unsigned int get16(const unsigned char *p) { return ((unsigned int)p[0]<<8)|p[1]; }
static void put16(unsigned char *p,unsigned int n) { p[0]=(unsigned char)(n>>8); p[1]=(unsigned char)n; }
static void put32(unsigned char *p,unsigned int n) { put16(p,n>>16); put16(p+2,n); }
int af_notice_owner_place(unsigned char *column,unsigned char *row,unsigned int item,Deposit callback,void *context) {
    unsigned int x=af_notice_owner_acre%5u+1u,z=af_notice_owner_acre/5u+1u;
    unsigned char *fg=af_notice_owner_foreground+512u*af_notice_owner_acre;
    unsigned char *flags=af_notice_owner_buried+32u*af_notice_owner_acre;
    ++af_notice_owner_place_calls;
    if (af_notice_owner_mode==1u) return 0;
    put32(column,x); put32(row,z);
    callback(fg,item,af_notice_owner_mode==8u ? 0u : x,z,flags,1u,context);
    if (af_notice_owner_mode==9u) callback(fg,item,x,z,flags,1u,context);
    return af_notice_owner_mode==2u ? 0 : 1;
}
void af_notice_owner_deposit(unsigned char *fg,unsigned int item,unsigned int x,unsigned int z,
                              unsigned char *flags,unsigned int count) {
    unsigned int unit=af_notice_owner_unit;
    (void)x; (void)z; (void)count;
    ++af_notice_owner_deposit_calls;
    if (af_notice_owner_mode==3u) return;
    put16(fg+2u*unit,item==0x2512u ? 0x2Au+af_notice_owner_hole : item);
    if (item!=0x2512u) put16(flags+2u*(unit/16u),get16(flags+2u*(unit/16u))|(1u<<(unit%16u)));
    if (af_notice_owner_mode==4u) put16(fg+2u*((unit+1u)%256u),0x1234u);
    if (af_notice_owner_mode==5u) flags[(2u*(unit/16u)+2u)%32u]^=1u;
    if (af_notice_owner_mode==6u) put16(fg+2u*unit,0xFFFFu);
}
void af_notice_owner_publish(const unsigned char *post) {
    ++af_notice_owner_post_calls;
    memcpy(af_notice_owner_board,post,104u);
}
void af_notice_owner_copy_rtc(unsigned char *destination,const unsigned char *source) {
    ++af_notice_owner_rtc_calls;
    memcpy(destination,source,8u);
}
