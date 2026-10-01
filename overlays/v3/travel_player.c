#include "travel_player.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
typedef __UINTPTR_TYPE__ address;
_Static_assert(AF_SAVE_PROFILE==192 && AF_SAVE_SURFACE_PROFILE==64 && AF_SAVE_STATE==1232,
    "Player transport requires the complete current ownership layout");
_Static_assert(AF_TP_BYTES<=0x4000,"Player record exceeds bounded Pak payload");
_Static_assert(AF_TP_CONSOLE_BYTES*4==6528,"Complete player console records");
enum { PRIVATE=0xBD0, SURFACE_PROFILE=192, CREATURE_PROFILE=256,
       DIARY_PROFILE=260, CARRIED_PROFILE=262, PAPER_MODE=263, ACCOUNT_PROFILE=264 };
struct View {
    const u8 *identity,*profile,*furniture,*clothing,*surfaces,*creatures;
    const u8 *rewards,*card,*account,*console,*diary;
    u8 paper;
};
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static int equal(const u8 *a,const u8 *b,u32 n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static int selection_valid(const u8 *p) {
    if(!p || (p[258]&254) || p[259] || p[CARRIED_PROFILE]>127 ||
       p[PAPER_MODE]>1 || p[ACCOUNT_PROFILE]>1)return 0;
    for(u32 i=265;i<AF_TP_PROFILE;i++)if(p[i])return 0;
    return 1;
}
static int bits(const u8 *owned,const u8 *selected,u32 bytes) {
    for(u32 i=0;i<bytes;i++)if(owned[i]&~selected[i])return 0;
    return 1;
}
static int calendar_valid(const u8 *c) {
    /* Same per-player calendar/lock contract as af_diary_valid. Shared holiday
     * header bytes are deliberately not part of the transported player record. */
    for(u32 i=0;i<24;i++)if(c[i*4]&128)return 0;
    return !c[96] && !(c[97]&128) && c[98]<=1 && !c[99] && c[102]<=12 &&
        !c[103] && ((c[100]|c[101]) || !c[102]);
}
static int records_valid(const struct View *v,const u8 *current) {
    const u8 *p=v->profile;
    if(!selection_valid(p) || !selection_valid(current))return AF_SAVE_FORMAT;
    if(!bits(p,current,263) || p[ACCOUNT_PROFILE]>current[ACCOUNT_PROFILE] ||
       p[PAPER_MODE]!=current[PAPER_MODE])return AF_SAVE_PROFILE_MISSING;
    if(!bits(v->furniture,p+32,128) || !bits(v->clothing,p+160,32) ||
       !bits(v->surfaces,p+SURFACE_PROFILE,64) || !bits(v->creatures,p+CREATURE_PROFILE,4))
        return AF_SAVE_CATALOGUE_INVALID;
    const u8 *r=v->rewards;
    if((r[0]&240) || r[4] || r[5] || r[6] || (r[7]&224) ||
       (r[8]&240) || r[9] || r[10] || r[11])return AF_SAVE_REWARD_INVALID;
    if(v->paper>1 || (v->paper && !(p[CARRIED_PROFILE]&1)))return AF_SAVE_CATALOGUE_INVALID;
    const u8 *c=v->card;
    u32 year=(u32)c[0]*256+c[1],birthday=c[5],giver=(u32)c[6]*256+c[7];
    if(!year && !c[2] && !c[3]) {if(c[4])return AF_SAVE_FORMAT;}
    else if(year<2000 || year>2099 || !c[3] ||
            c[3]>af_diary_days(year,c[2]) || c[4]>AF_HC_STAMPS)return AF_SAVE_FORMAT;
    /* The top bit belongs to the town's first golden gifts, not this player. */
    if(birthday>100 || (giver && (!birthday || giver>>12!=14 || giver==0xEFFF)))return AF_SAVE_FORMAT;
    if(!calendar_valid(v->diary))return AF_SAVE_FORMAT;
    const u8 *a=v->account;
    if(word(a)>AF_BANK_MAX || (a[4]&~0x3Cu) || a[5] || a[6] || a[7] ||
       (!p[ACCOUNT_PROFILE] && (word(a) || a[4])))return AF_SAVE_FORMAT;
    return AF_SAVE_OK;
}
static struct View wire_view(const u8 *p) {
    return (struct View){p+16,p+AF_TP_HEADER,p+AF_TP_FURNITURE,p+AF_TP_CLOTHING,
        p+AF_TP_SURFACES,p+AF_TP_CREATURES,p+AF_TP_REWARDS,p+AF_TP_CARD,
        p+AF_TP_ACCOUNT,p+AF_TP_CONSOLE,p+AF_TP_DIARY,p[AF_TP_PAPER]};
}
int af_v3_player_records_valid(const u8 *p,u32 bytes,const AFTravelSelection *current) {
    if(!p || bytes!=AF_TP_BYTES || !current)return AF_SAVE_ARGUMENT;
    if(word(p)!=0x41465031u || word(p+4)!=1 || word(p+8)!=AF_TP_BYTES || word(p+12))return AF_SAVE_FORMAT;
    for(u32 i=AF_TP_ACCOUNT+8;i<AF_TP_CONSOLE;i++)if(p[i])return AF_SAVE_FORMAT;
    struct View v=wire_view(p);return records_valid(&v,current->bytes);
}
static int town_valid(const AFTravelTown *t,const AFTravelSelection *s) {
    if(!t || !s || !t->players || !t->working || !t->console || !t->cards || !t->diary)return 0;
    const void *p[6]={t->players,t->working,t->console,t->cards,t->diary,t->accounts};
    const u32 n[6]={4*PRIVATE,AF_SAVE_STATE,4*AF_TP_CONSOLE_BYTES,AF_HC_BYTES,AF_DIARY_BYTES,
        t->accounts?AF_BANK_BYTES:0};
    for(u32 i=0;i<6;i++) {
        if(n[i] && (!separate(p[i],n[i],t,sizeof(*t)) || !separate(p[i],n[i],s,sizeof(*s))))return 0;
        for(u32 j=0;j<i;j++)
            if(n[i] && n[j] && !separate(p[i],n[i],p[j],n[j]))return 0;
    }
    if(
       !selection_valid(s->bytes) || !af_holiday_cards_valid(t->cards) ||
       t->cards[4]!=AF_HC_CARRIED_WIRE || !af_diary_valid(t->diary) ||
       !equal(t->working,s->bytes,192) ||
       !equal(t->working+AF_SAVE_SURFACE_OFFSET,s->bytes+SURFACE_PROFILE,64) ||
       !equal(t->working+AF_SAVE_CREATURE_OFFSET,s->bytes+CREATURE_PROFILE,4) ||
       t->cards[8]!=s->bytes[CARRIED_PROFILE] ||
       (t->cards[15]&1)!=s->bytes[PAPER_MODE] ||
       (s->bytes[ACCOUNT_PROFILE] && !t->accounts) ||
       (t->accounts && (!af_bank_valid(t->accounts,AF_BANK_BYTES) ||
        t->accounts[8]!=s->bytes[ACCOUNT_PROFILE])))return 0;
    return 1;
}
static int external(const u8 *p,u32 bytes,const AFTravelTown *t,const AFTravelSelection *s) {
    return separate(p,bytes,t,sizeof(*t)) && separate(p,bytes,s,sizeof(*s)) &&
        separate(p,bytes,t->players,4*PRIVATE) && separate(p,bytes,t->working,AF_SAVE_STATE) &&
        separate(p,bytes,t->console,4*AF_TP_CONSOLE_BYTES) && separate(p,bytes,t->cards,AF_HC_BYTES) &&
        separate(p,bytes,t->diary,AF_DIARY_BYTES) &&
        (!t->accounts || separate(p,bytes,t->accounts,AF_BANK_BYTES));
}
int af_v3_player_export(u8 *out,u32 bytes,const AFTravelTown *t,u32 slot,const AFTravelSelection *s) {
    if(!out || bytes!=AF_TP_BYTES || slot>=4 || !town_valid(t,s) ||
       !external(out,bytes,t,s))return AF_SAVE_ARGUMENT;
    u8 card[8],account[8]={0};copy(card,t->cards+16+slot*8,8);card[5]&=127;
    if(t->accounts)copy(account,t->accounts+16+slot*8,8);
    struct View v={t->players+slot*PRIVATE,s->bytes,t->working+AF_SAVE_PROFILE+slot*128,
        t->working+AF_SAVE_PROFILE+512+slot*32,
        t->working+AF_SAVE_SURFACE_OFFSET+64+slot*64,t->working+AF_SAVE_CREATURE_OFFSET+4+slot*4,
        t->working+AF_SAVE_REWARD_OFFSET+slot*12,card,account,t->console+slot*AF_TP_CONSOLE_BYTES,
        t->diary->bytes+AF_DIARY_HEADER+slot*AF_DIARY_PLAYER,t->cards[9+slot]};
    int r=records_valid(&v,s->bytes);if(r<0)return r;
    for(u32 i=0;i<bytes;i++)out[i]=0;
    put(out,0x41465031u);put(out+4,1);put(out+8,bytes);copy(out+16,v.identity,16);
    copy(out+AF_TP_HEADER,v.profile,AF_TP_PROFILE);copy(out+AF_TP_FURNITURE,v.furniture,128);
    copy(out+AF_TP_CLOTHING,v.clothing,32);copy(out+AF_TP_SURFACES,v.surfaces,64);
    copy(out+AF_TP_CREATURES,v.creatures,4);copy(out+AF_TP_REWARDS,v.rewards,12);
    out[AF_TP_PAPER]=v.paper;copy(out+AF_TP_CARD,v.card,8);copy(out+AF_TP_ACCOUNT,v.account,8);
    copy(out+AF_TP_CONSOLE,v.console,AF_TP_CONSOLE_BYTES);copy(out+AF_TP_DIARY,v.diary,AF_DIARY_PLAYER);
    return AF_SAVE_OK;
}
int af_v3_player_restore(AFTravelTown *t,u32 slot,const u8 *p,u32 bytes,const AFTravelSelection *s) {
    if(slot>=4 || !town_valid(t,s) || !p || bytes!=AF_TP_BYTES || !external(p,bytes,t,s))return AF_SAVE_ARGUMENT;
    int r=af_v3_player_records_valid(p,bytes,s);if(r<0)return r;
    struct View v=wire_view(p);
    if(!equal(t->players+slot*PRIVATE,v.identity,16))return AF_SAVE_BINDING;
    u8 *f=t->working+AF_SAVE_PROFILE+slot*128,*c=t->working+AF_SAVE_PROFILE+512+slot*32;
    u8 *surface=t->working+AF_SAVE_SURFACE_OFFSET+64+slot*64;
    u8 *creature=t->working+AF_SAVE_CREATURE_OFFSET+4+slot*4;
    u8 *reward=t->working+AF_SAVE_REWARD_OFFSET+slot*12;
    /* Ownership is monotonic. Progress and editable pages use the traveller's
     * current record. Do not overwrite the host's profiles or any town flags. */
    for(u32 i=0;i<128;i++)f[i]|=v.furniture[i];
    for(u32 i=0;i<32;i++)c[i]|=v.clothing[i];
    for(u32 i=0;i<64;i++)surface[i]|=v.surfaces[i];
    for(u32 i=0;i<4;i++)creature[i]|=v.creatures[i];
    for(u32 i=0;i<12;i++)reward[i]|=v.rewards[i];
    t->cards[9+slot]|=v.paper;
    u8 first=t->cards[21+slot*8]&128u;
    copy(t->cards+16+slot*8,v.card,8);t->cards[21+slot*8]|=first;
    if(t->accounts)copy(t->accounts+16+slot*8,v.account,8);
    copy(t->console+slot*AF_TP_CONSOLE_BYTES,v.console,AF_TP_CONSOLE_BYTES);
    copy(t->diary->bytes+AF_DIARY_HEADER+slot*AF_DIARY_PLAYER,v.diary,AF_DIARY_PLAYER);
    return AF_SAVE_OK;
}
int af_v3_player_collect(u8 *p,u32 bytes,const u8 identity[16],u32 item,u32 mark,
    const AFTravelSelection *s) {
    if(!identity || mark>1)return AF_SAVE_ARGUMENT;
    int r=af_v3_player_records_valid(p,bytes,s);if(r<0)return r;
    if(!equal(p+16,identity,16))return AF_SAVE_BINDING;
    u32 owned,profile,index;
    if((item&0xFF00)==0x3400 && item<=0x34FF) {
        owned=AF_TP_CLOTHING;profile=AF_TP_HEADER+160;index=item&255;
    } else if(item>=0x3000 && item<=0x3FFF) {
        owned=AF_TP_FURNITURE;profile=AF_TP_HEADER+32;index=(item&0xFFF)>>2;
    } else if((item>>8)-0x26u<2u && (item&255)>=64) {
        owned=AF_TP_SURFACES;profile=AF_TP_HEADER+SURFACE_PROFILE;
        index=((item>>8)-0x26u)*256u+(item&255);
    } else if((item>=0x2320 && item<=0x2328) || (item>=0x2D20 && item<=0x2D27)) {
        owned=AF_TP_CREATURES;profile=AF_TP_HEADER+CREATURE_PROFILE;
        index=item<0x2D00?item-0x2320:item-0x2D20+9;
    } else return AF_SAVE_ARGUMENT;
    u32 byte=index>>3,bit=1u<<(index&7);
    if(!(p[profile+byte]&bit))return AF_SAVE_PROFILE_MISSING;
    if(mark)p[owned+byte]|=(u8)bit;
    return !!(p[owned+byte]&bit);
}
int af_v3_player_paper(u8 *p,u32 bytes,const u8 identity[16],u32 mark,const AFTravelSelection *s) {
    if(!identity || mark>1)return AF_SAVE_ARGUMENT;
    int r=af_v3_player_records_valid(p,bytes,s);if(r<0)return r;
    if(!equal(p+16,identity,16))return AF_SAVE_BINDING;
    if(!(p[AF_TP_HEADER+CARRIED_PROFILE]&1))return AF_SAVE_PROFILE_MISSING;
    if(mark)p[AF_TP_PAPER]=1;
    return p[AF_TP_PAPER];
}
