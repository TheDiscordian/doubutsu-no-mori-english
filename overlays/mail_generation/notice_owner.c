#include "notice_owner.h"

typedef void (*Deposit)(unsigned char *, unsigned int, unsigned int, unsigned int,
                        unsigned char *, unsigned int, void *);

#ifdef __mips__
#define foreground ((unsigned char *)0x8012D148u)
#define buried ((unsigned char *)0x801362DCu)
#define timestamp ((unsigned char *)0x8013673Cu)
#define board ((unsigned char *)0x80129E0Au)
#define place ((int (*)(unsigned char *, unsigned char *, unsigned int, Deposit, void *))0x8008EA5Cu)
#define deposit ((void (*)(unsigned char *, unsigned int, unsigned int, unsigned int, unsigned char *, unsigned int))0x800A3E34u)
#define publish ((void (*)(const unsigned char *))0x800A5D30u)
#define copy_rtc ((void (*)(unsigned char *, const unsigned char *))0x800D5D6Cu)
#else
extern unsigned char af_notice_owner_foreground[15360], af_notice_owner_buried[960];
extern unsigned char af_notice_owner_timestamp[8], af_notice_owner_board[1560];
extern int af_notice_owner_place(unsigned char *, unsigned char *, unsigned int, Deposit, void *);
extern void af_notice_owner_deposit(unsigned char *, unsigned int, unsigned int, unsigned int,
                                     unsigned char *, unsigned int);
extern void af_notice_owner_publish(const unsigned char *);
extern void af_notice_owner_copy_rtc(unsigned char *, const unsigned char *);
#define foreground af_notice_owner_foreground
#define buried af_notice_owner_buried
#define timestamp af_notice_owner_timestamp
#define board af_notice_owner_board
#define place af_notice_owner_place
#define deposit af_notice_owner_deposit
#define publish af_notice_owner_publish
#define copy_rtc af_notice_owner_copy_rtc
#endif

typedef struct {
    unsigned char *before, *fg, *flags;
    unsigned int item, called, success, unit;
} Burial;

static unsigned int read16(const unsigned char *p) { return ((unsigned int)p[0]<<8)|p[1]; }
static unsigned int read32(const unsigned char *p) { return (read16(p)<<16)|read16(p+2); }
static void write16(unsigned char *p, unsigned int n) { p[0]=(unsigned char)(n>>8); p[1]=(unsigned char)n; }
static void write32(unsigned char *p, unsigned int n) { write16(p,n>>16); write16(p+2,n); }

static void restore_acre(Burial *b) {
    unsigned int i;
    if (!b->fg) return;
    for (i=0; i<512u; ++i) b->fg[i]=b->before[i];
    for (i=0; i<32u; ++i) b->flags[i]=b->before[512u+i];
    b->success=0;
}

static void capture_deposit(unsigned char *fg, unsigned int item, unsigned int column,
                            unsigned int row, unsigned char *flags, unsigned int count, void *opaque) {
    Burial *b=(Burial *)opaque;
    unsigned int acre, i, changed=0, value, expected;
    if (b->called++) { restore_acre(b); return; }
    if (!column || column>5u || !row || row>6u || !count || count>255u || item!=b->item) return;
    acre=(row-1u)*5u+column-1u;
    if (fg!=foreground+acre*512u || flags!=buried+acre*32u) return;
    b->fg=fg; b->flags=flags;
    for (i=0; i<512u; ++i) b->before[i]=fg[i];
    for (i=0; i<32u; ++i) b->before[512u+i]=flags[i];
    deposit(fg,item,column,row,flags,count);
    for (i=0; i<256u; ++i) {
        if (read16(fg+2u*i)!=read16(b->before+2u*i)) { ++changed; b->unit=i; }
    }
    if (changed!=1u || read16(b->before+2u*b->unit)) { restore_acre(b); return; }
    value=read16(fg+2u*b->unit);
    if (item==0x2512u ? (value<0x2Au || value>0x42u) : value!=item) { restore_acre(b); return; }
    for (i=0; i<16u; ++i) {
        expected=read16(b->before+512u+2u*i);
        if (item!=0x2512u && i==b->unit/16u) expected|=1u<<(b->unit%16u);
        if (read16(flags+2u*i)!=expected) { restore_acre(b); return; }
    }
    b->success=1;
}

static int undo_matches(const unsigned char *frame, unsigned int item) {
    unsigned int column=read32(frame+0x60), row=read32(frame+0x5C), acre, tile, delta, flag, expected;
    const unsigned char *undo=frame+0xD0;
    if (!column || column>5u || !row || row>6u || read16(undo+14)!=0x4E54u || read16(undo+8)) return 0;
    acre=(row-1u)*5u+column-1u;
    tile=read32(undo); flag=read32(undo+4);
    delta=tile-(0x8012D148u+acre*512u);
    if (delta>=512u || (delta&1u) || flag!=0x801362DCu+acre*32u+(delta/32u)*2u) return 0;
    expected=read16(undo+10);
    if (item!=0x2512u) expected|=1u<<((delta/2u)%16u);
    return (item==0x2512u ? (read16(undo+12)>=0x2Au && read16(undo+12)<=0x42u) : read16(undo+12)==item)
        && read16(foreground+acre*512u+delta)==read16(undo+12)
        && read16(buried+acre*32u+(delta/32u)*2u)==expected;
}

int af_notice_owner_create(AfNpcMailCreateWork *work, unsigned char *destination,
                            AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request;
    unsigned char *frame, *undo;
    unsigned char descriptor[12] __attribute__((aligned(4)));
    unsigned int item, i, phase, acre;
    Burial transaction;
    int result;
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session=&work->captured.session; request=session->animal;
    if (!request || session->remail) return af_notice_treasure_create(work,destination,active,capital);
    if ((__UINTPTR_TYPE__)request&1u) return 0;
    if (request[11]!=244u) return af_notice_treasure_create(work,destination,active,capital);
    if (!session->player || session->condition || session->foreign || read32(request)!=0x41464E52u
            || request[9] || request[10] || (request[8]!=1u && request[8]!=2u)
            || (__UINTPTR_TYPE__)request>(~(__UINTPTR_TYPE__)0)-376u
            || (__UINTPTR_TYPE__)destination>(~(__UINTPTR_TYPE__)0)-544u) return 0;
    frame=(unsigned char *)((__UINTPTR_TYPE__)request+24u);
    if (((__UINTPTR_TYPE__)frame&7u) || (__UINTPTR_TYPE__)frame!=(__UINTPTR_TYPE__)destination+192u
            || read32(request+4)!=(unsigned int)(__UINTPTR_TYPE__)frame
            || !af_mail_create_guard(work,destination,active,capital,frame,352u)
            || !af_mail_create_guard(work,destination,active,capital,foreground,15360u)
            || !af_mail_create_guard(work,destination,active,capital,buried,960u)
            || !af_mail_create_guard(work,destination,active,capital,board,1560u)
            || !af_mail_create_guard(work,destination,active,capital,timestamp,8u)) return 0;
    item=read16(frame+0x66); phase=request[8]; undo=frame+0xD0;
    if (!item) return 0;
    if (phase==1u) {
        /* Character access to this object's representation is intentional. No
         * generation/catalogue members are read while it is burial scratch.
         * Phase two's complete creator resets it before typed use resumes.
         */
        transaction.before=(unsigned char *)&work->generation;
        transaction.fg=0; transaction.flags=0; transaction.item=item;
        transaction.called=0; transaction.success=0; transaction.unit=0;
        result=place(frame+0x60,frame+0x5C,item,capture_deposit,&transaction);
        if (result!=1 || transaction.called!=1u || !transaction.success) { restore_acre(&transaction); return 0; }
        acre=(unsigned int)(transaction.fg-foreground)/512u;
        write32(undo,0x8012D148u+acre*512u+2u*transaction.unit);
        write32(undo+4,0x801362DCu+acre*32u+2u*(transaction.unit/16u));
        write16(undo+8,read16(transaction.before+2u*transaction.unit));
        write16(undo+10,read16(transaction.before+512u+2u*(transaction.unit/16u)));
        write16(undo+12,read16(transaction.fg+2u*transaction.unit));
        write16(undo+14,0x4E54u);
        for (i=0; i<164u; ++i) destination[i]=0;
        return 1;
    }
    if (!undo_matches(frame,item) || read32(frame+0x10)>65535u) return 0;
    write32(descriptor,0x41464E54u);
    write16(descriptor+4,read32(frame+0x10)); write16(descriptor+6,item);
    descriptor[8]=(unsigned char)read32(frame+0x5C); descriptor[9]=(unsigned char)read32(frame+0x60);
    descriptor[10]=0; descriptor[11]=245u;
    session->animal=descriptor;
    result=af_notice_treasure_create(work,destination,active,capital);
    session->animal=request;
    if (!result) return 0;
    for (i=0; i<96u; ++i) frame[0x68u+i]=destination[i];
    publish(frame+0x68);
    copy_rtc(timestamp,frame+0x140);
    return 1;
}
