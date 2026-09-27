#include "console_save.h"

typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ address;
enum { HEADER = 32, STRIDE = 64, GAMES = 19, DATA = HEADER + GAMES * STRIDE,
       OP_BYTES = 16, ACTIVE = 0x41464E53 };

static u32 word(const u8 *p) {
    return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];
}
static u32 half(const u8 *p) { return ((u32)p[0]<<8)|p[1]; }
static void put(u8 *p, u32 v) {
    p[0]=v>>24; p[1]=v>>16; p[2]=v>>8; p[3]=v;
}
static void copy(u8 *d, const u8 *s, u32 n) { while(n--) *d++=*s++; }
static void fill(u8 *d, u8 v, u32 n) { while(n--) *d++=v; }
static int equal(const u8 *a, const u8 *b, u32 n) {
    while(n--) if(*a++!=*b++) return 0;
    return 1;
}
static int range(u32 offset, u32 length, u32 size) {
    return offset<=size && length<=size-offset;
}
static int data_range(u32 offset, u32 length, u32 size) {
    return offset>=DATA && !(offset&15) && length && range(offset,length,size);
}
static int valid_image(const u8 *p, u32 length, u32 kind, u32 mapper) {
    u32 i, expected;
    if(kind==2) return mapper==0xFFFFFFFF && length==65536 &&
        equal(p,(const u8 *)"\1*NINTENDO-HVC*",15);
    if(kind!=1 || length<16 || word(p)!=0x4E45531A || !p[4] || (p[7]&15)) return 0;
    for(i=8;i<16;i++) if(p[i]) return 0;
    expected=16u+((p[6]&4)?512u:0u)+p[4]*16384u+p[5]*8192u;
    return length==expected && mapper==((p[7]&240)|(p[6]>>4)) &&
        (mapper==0 || mapper==1 || mapper==4 || mapper==9);
}

int af_v3_console_validate(const u8 *packet, u32 bytes) {
    u8 used[(AF_CONSOLE_PAYLOAD_BYTES+7)/8];
    u32 game, game_bits=0, total_ops=0, extent=0;
    if(!packet || bytes<DATA || bytes>0x800000) return AF_CONSOLE_BAD_ARGUMENT;
    if(word(packet)!=0x41464E45 || word(packet+4)!=1 || word(packet+8)!=GAMES ||
       word(packet+12)!=STRIDE || word(packet+16)!=DATA ||
       word(packet+20)!=AF_CONSOLE_PAYLOAD_BYTES || word(packet+24)!=8 ||
       word(packet+28)!=bytes) return AF_CONSOLE_BAD_PACKET;
    fill(used,0,sizeof(used));
    for(game=0;game<GAMES;game++) {
        const u8 *e=packet+HEADER+game*STRIDE;
        u32 n=word(e+44), ops=word(e+40), bit=word(e+48), i, end=0, had_battery=0;
        if(word(e)!=game+1 || word(e+12) || word(e+56) || word(e+60) || bit>=32 ||
           (game_bits&(1u<<bit)) || n>AF_CONSOLE_MAX_OPS ||
           (n ? !data_range(ops,n*OP_BYTES,bytes) : ops!=0) ||
           !data_range(word(e+16),word(e+20),bytes) ||
           !data_range(word(e+24),word(e+28),bytes) ||
           !data_range(word(e+32),word(e+36),bytes)) return AF_CONSOLE_BAD_PACKET;
        if(!valid_image(packet+word(e+16),word(e+20),word(e+4),word(e+8)))
            return AF_CONSOLE_BAD_PACKET;
        game_bits|=1u<<bit;
        for(i=0;i<n;i++) {
            const u8 *op=packet+ops+i*OP_BYTES;
            u32 size=half(op+2), to=word(op+4), from=word(op+8), defaults=word(op+12), j;
            if(op[0]==4) {
                if(op[1]!=1 || size || to || from || defaults || !had_battery)
                    return AF_CONSOLE_BAD_PACKET;
                continue;
            }
            if(op[1] || !size || !range(to,size,AF_CONSOLE_PAYLOAD_BYTES))
                return AF_CONSOLE_BAD_PACKET;
            if(op[0]==1) {
                if((from&~0x87FFu) || !range(from&0x7FF,size,AF_CONSOLE_WORK_BYTES) ||
                   !data_range(defaults,size,bytes)) return AF_CONSOLE_BAD_PACKET;
            } else if(op[0]==2) {
                if(defaults || !range(from,size,AF_CONSOLE_BATTERY_BYTES)) return AF_CONSOLE_BAD_PACKET;
                had_battery=1;
            } else if(op[0]==3) {
                if(defaults || word(e+4)!=2 || !range(from,size,word(e+20))) return AF_CONSOLE_BAD_PACKET;
            } else return AF_CONSOLE_BAD_PACKET;
            for(j=to;j<to+size;j++) {
                if(used[j>>3]&(1u<<(j&7))) return AF_CONSOLE_BAD_PACKET;
                used[j>>3]|=1u<<(j&7);
            }
            if(end<to+size) end=to+size;
        }
        if(word(e+52)!=end) return AF_CONSOLE_BAD_PACKET;
        if(extent<end) extent=end;
        total_ops+=n;
    }
    return total_ops==60 && extent==AF_CONSOLE_PAYLOAD_BYTES ? 0 : AF_CONSOLE_BAD_PACKET;
}

static int overlap(const void *a, u32 an, const void *b, u32 bn) {
    address x=(address)a,y=(address)b;
    return x<=y ? y-x<an : x-y<bn;
}
static u32 sum(const u8 *p, u32 n) {
    u32 s=0;
    while(n--) s+=*p++;
    return s;
}
static void zelda(u8 *b) {
    u32 i;
    b[0]=0; b[1]=0x5A;
    fill(b+0x52A,0xFF,3); fill(b+0x52D,0,3);
    fill(b+0x51E,0x5A,3); fill(b+0x521,0xA5,3);
    for(i=0;i<3;i++) {
        u32 checksum=sum(b+2+i*8,8)+sum(b+0x1A+i*0x28,0x28)+
            sum(b+0x92+i*0x180,0x180)+b[0x512+i]+b[0x515+i]+b[0x518+i]+b[0x51B+i];
        b[0x524+i*2]=checksum>>8; b[0x525+i*2]=checksum;
    }
}

int af_v3_console_open(AFConsoleSave *s, const u8 *packet, u32 bytes,
    u32 game, u32 player, u8 *save, u32 save_bytes,
    u8 *work, u32 work_bytes, u8 *battery, u32 battery_bytes,
    u8 *image, u32 image_bytes) {
    const void *buffers[6]; u32 lengths[6],i,j,bit,first;
    const u8 *entry;
    int result;
    if(!s || !save || !work || !battery || !image || player>=AF_CONSOLE_PLAYERS ||
       save_bytes!=AF_CONSOLE_SAVE_BYTES || work_bytes!=AF_CONSOLE_WORK_BYTES ||
       battery_bytes!=AF_CONSOLE_BATTERY_BYTES) return AF_CONSOLE_BAD_ARGUMENT;
    if(!game || game>GAMES) return AF_CONSOLE_BAD_GAME;
    result=af_v3_console_validate(packet,bytes);
    if(result<0) return result;
    entry=packet+HEADER+(game-1)*STRIDE;
    if(image_bytes!=word(entry+20)) return AF_CONSOLE_BAD_ARGUMENT;
    buffers[0]=s; lengths[0]=sizeof(*s); buffers[1]=packet; lengths[1]=bytes;
    buffers[2]=save; lengths[2]=save_bytes; buffers[3]=work; lengths[3]=work_bytes;
    buffers[4]=battery; lengths[4]=battery_bytes; buffers[5]=image; lengths[5]=image_bytes;
    for(i=0;i<6;i++) {
        if(lengths[i]>(address)-1-(address)buffers[i]) return AF_CONSOLE_BAD_ARGUMENT;
        for(j=0;j<i;j++) if(overlap(buffers[i],lengths[i],buffers[j],lengths[j]))
            return AF_CONSOLE_BAD_ARGUMENT;
    }
    /* All error exits precede writes. Never reuse another player's save bytes. */
    fill((u8 *)s,0,sizeof(*s));
    s->packet=packet; s->operations=word(entry+44)?packet+word(entry+40):0;
    s->operation_count=word(entry+44); s->image_bytes=image_bytes;
    s->save=save+player*AF_CONSOLE_PLAYER_BYTES;
    s->work=work; s->battery=battery; s->image=image;
    copy(image,packet+word(entry+16),image_bytes);
    bit=1u<<word(entry+48); first=!(word(s->save+4)&bit);
    put(s->save+4,word(s->save+4)|bit);
    for(i=0;i<s->operation_count;i++) {
        const u8 *op=s->operations+i*OP_BYTES;
        u32 n=half(op+2),from=word(op+8);
        u8 *saved=s->save+8+word(op+4);
        if(op[0]==1 && first) copy(saved,packet+word(op+12),n);
        else if(op[0]==2) {
            if(first) fill(battery+from,0,n);
            else copy(battery+from,saved,n);
        } else if(op[0]==3 && !first) copy(image+from,saved,n);
        else if(op[0]==4 && !first) zelda(battery);
    }
    s->active=ACTIVE;
    return first ? 1 : 0;
}

int af_v3_console_frame(AFConsoleSave *s, int reset) {
    u32 i; int changed=0;
    if(!s || s->active!=ACTIVE || (reset!=0 && reset!=1)) return AF_CONSOLE_BAD_STATE;
    for(i=0;i<s->operation_count;i++) if(s->operations[i*OP_BYTES]==1) {
        const u8 *op=s->operations+i*OP_BYTES;
        u32 n=half(op+2),from=word(op+8);
        u8 *flag=s->score_state+i, *saved=s->save+8+word(op+4), *work=s->work+(from&0x7FF);
        const u8 *defaults=s->packet+word(op+12);
        if(reset) {
            if(*flag==1 && !(from&0x8000)) *flag=0;
        } else {
            if(*flag==3) { copy(saved,defaults,n); *flag=0; }
            if(!*flag) {
                if(equal(work,defaults,n)) { copy(work,saved,n); *flag=1; }
            } else if(!equal(work,saved,n)) { copy(saved,work,n); changed=1; }
        }
    }
    return changed;
}

int af_v3_console_close(AFConsoleSave *s) {
    u32 i; int changed=0;
    if(!s || s->active!=ACTIVE) return AF_CONSOLE_BAD_STATE;
    for(i=0;i<s->operation_count;i++) {
        const u8 *op=s->operations+i*OP_BYTES;
        u32 n=half(op+2);
        if(op[0]==2 || op[0]==3) {
            const u8 *from=(op[0]==2?s->battery:s->image)+word(op+8);
            u8 *to=s->save+8+word(op+4);
            if(!equal(to,from,n)) { copy(to,from,n); changed=1; }
        }
    }
    s->active=0;
    return changed;
}
