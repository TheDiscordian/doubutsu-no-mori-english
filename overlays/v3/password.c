/* Portable GAFE01-r0 code transform. Tables come from the supplied disc.
 * Algorithm reference: ac-decomp m_mail_password_check.c (CC0).
 * No game state, heap, RNG, unchecked pointers, or per-item rules live here. */
#include "password.h"
typedef af_pw_u8 u8;
typedef af_pw_u32 u32;
enum { ALPH=32, SUB=96, PRIME=352, SELECT=864, KEYS=992, TEXT=1120 };
static u32 be16(const u8 *p) { return (u32)p[0]*256+p[1]; }
static void copy(u8 *d,const u8 *s,u32 n) { while(n--) *d++=*s++; }
static int tables_ok(const u8 *t,u32 n) {
    u32 i,j;
    if(!t||n<TEXT||n>65535||t[0]!='A'||t[1]!='F'||t[2]!='P'||t[3]!='W'
        ||be16(t+4)!=1||be16(t+6)!=n||be16(t+8)!=64||be16(t+10)!=256
        ||be16(t+12)!=16||be16(t+14)!=32||be16(t+16)!=TEXT||be16(t+18)!=n-TEXT) return 0;
    for(i=20;i<32;i++) if(t[i]) return 0;
    if(be16(t+PRIME)!=17||be16(t+PRIME+2)!=19||be16(t+PRIME+4)!=23) return 0;
    for(i=0;i<256;i++) {
        u32 p=be16(t+PRIME+i*2);
        if(p<17||p>1667) return 0;
        for(j=0;j<i;j++) if(t[SUB+i]==t[SUB+j]) return 0;
    }
    for(i=0;i<64;i++) for(j=0;j<i;j++) if(t[ALPH+i]==t[ALPH+j]) return 0;
    for(i=0;i<128;i++) {
        u32 v=t[SELECT+i];
        if(v>19||v==5||v==13||v==15) return 0;
        for(j=i&~7u;j<i;j++) if(t[SELECT+j]==v) return 0;
    }
    for(i=0;i<32;i++) {
        u32 a=be16(t+KEYS+i*4),b=be16(t+KEYS+i*4+2);
        if(a<TEXT||!b||b>32||a>n||b>n-a) return 0;
    }
    return 1;
}
static void transpose(u8 *p,const u8 *t,u32 stage,int direction) {
    u32 key=stage?9:18,k=(stage*16+(p[key]&15))*4;
    u32 a=be16(t+KEYS+k),n=be16(t+KEYS+k+2),i,j=0;
    for(i=0;i<21;i++) if(i!=key) { p[i]=(u8)(p[i]+direction*(int)t[a+j]);j=(j+1)%n; }
}
static void shuffle(u8 *p,const u8 *t,u32 stage,int decode) {
    u8 input[20],output[20];u32 key=stage?2:13,n=stage?20:19,i,b,a,j=0;
    const u8 *offset=t+SELECT+(p[key]&3)*8;
    for(i=0;i<21;i++) if(i!=key) input[j++]=p[i];
    for(i=0;i<20;i++) output[i]=0;
    for(i=0;i<n;i++) for(b=0;b<8;b++) {
        a=(i+offset[b])%n;
        if(decode) output[i]|=(u8)(input[a]&(1u<<b));
        else output[a]|=(u8)(input[i]&(1u<<b));
    }
    j=0;for(i=0;i<21;i++) if(i!=key) p[i]=output[j++];
    /* Stage zero's last scratch byte is unused: RSA overwrites it during
     * encoding, and decoding consumes only the first twenty payload bytes. */
}
static void rotate(u8 *p,int shift) {
    u8 input[20],output[20];u32 i,b,j=0;int target;
    for(i=0;i<21;i++) if(i!=1) input[j++]=p[i];
    for(i=0;i<20;i++) output[i]=0;
    for(i=0;i<160;i++) {
        target=((int)i+shift+160)%160;b=(input[i/8]>>(i%8))&1;
        output[(u32)target/8]|=(u8)(b<<((u32)target%8));
    }
    j=0;for(i=0;i<21;i++) if(i!=1) p[i]=output[j++];
}
static void invert(u8 *p) { u32 i;for(i=0;i<21;i++) if(i!=1) p[i]^=255; }
static void reverse(u8 *p) {
    u8 v[20];u32 i,b,j=0;
    for(i=0;i<21;i++) if(i!=1) v[j++]=p[i];
    j=0;for(i=0;i<21;i++) if(i!=1) {
        p[i]=0;for(b=0;b<8;b++) p[i]|=(u8)(((v[19-j]>>b)&1)<<(7-b));j++;
    }
}
static void mix(u8 *p,int decode) {
    int k=p[1]&15;
    if(decode) {
        if(k>12) { rotate(p,-k*3);invert(p);reverse(p); }
        else if(k>8) { rotate(p,k*5);reverse(p); }
        else if(k>4) { invert(p);rotate(p,k*5); }
        else { reverse(p);rotate(p,-k*3); }
    } else {
        if(k>12) { reverse(p);invert(p);rotate(p,k*3); }
        else if(k>8) { reverse(p);rotate(p,-k*5); }
        else if(k>4) { rotate(p,-k*5);invert(p); }
        else { rotate(p,k*3);reverse(p); }
    }
}
static u32 power(u32 base,u32 exponent,u32 modulus) {
    u32 result=1;base%=modulus;
    while(exponent) { if(exponent&1) result=(result*base)%modulus;base=(base*base)%modulus;exponent>>=1; }
    return result;
}
static int rsa(u8 *p,const u8 *t,int decode) {
    u32 a=p[15]&3,b=(p[15]>>2)&3,r=be16(t+PRIME+p[5]*2),i,v,n,e=r,mask=p[20],saved=0;
    const u8 *selected=t+SELECT+(p[15]>>4)*8;
    if(a==3) { a=(a^b)&3;if(a==3)a=0; }
    if(b==3) { b=(a+1)&3;if(b==3)b=1; }
    if(a==b) { b=(a+1)&3;if(b==3)b=1; }
    a=be16(t+PRIME+a*2);b=be16(t+PRIME+b*2);n=a*b;
    if(decode) {
        u32 phi=(a-1)*(b-1);
        for(e=1;e<phi;e++) if((r*e)%phi==1) break;
        if(e==phi) return 0;
    }
    for(i=0;i<8;i++) {
        v=p[selected[i]];
        if(decode) v|=((mask>>i)&1)<<8;
        v=power(v,e,n);p[selected[i]]=(u8)v;saved|=((v>>8)&1)<<i;
    }
    if(!decode) p[20]=(u8)saved;
    return 1;
}
int af_v3_password_decode(const u8 *t,u32 size,const u8 *text,u32 length,af_v3_password *out) {
    u8 six[28],p[21];af_v3_password value;u32 i,j,bit,total=0;u8 c;
    if(!text||!out||length!=28||!tables_ok(t,size)) return 0;
    for(i=0;i<28;i++) {
        c=text[i];if(c=='0')c='O';if(c=='1')c='l';if(c=='#')c=209;
        for(j=0;j<64;j++) if(t[ALPH+j]==c) break;
        if(j==64) return 0;
        six[i]=(u8)j;
    }
    for(i=0;i<21;i++) p[i]=0;
    for(bit=0;bit<168;bit++) p[bit/8]|=(u8)(((six[bit/6]>>(bit%6))&1)<<(bit%8));
    transpose(p,t,1,-1);shuffle(p,t,1,1);mix(p,1);
    if(!rsa(p,t,1)) return 0;
    shuffle(p,t,0,1);transpose(p,t,0,1);
    for(i=0;i<20;i++) { for(j=0;j<256;j++) if(t[SUB+j]==p[i])break;p[i]=(u8)j; }
    value.item=(af_pw_u16)be16(p+18);value.type=p[0]>>5;value.checksum=(p[0]>>3)&3;
    value.hit_rate_index=(p[0]>>1)&3;value.npc_type=255;value.npc_code=255;value.reserved=0;
    if(value.type>=6) return 0;
    if(value.type==1||value.type==2) { value.npc_type=p[0]&1;value.npc_code=p[1]; }
    if(value.type==3) value.hit_rate_index|=(p[0]&1)<<2;
    copy(value.str0,p+2,8);copy(value.str1,p+10,8);
    for(i=2;i<18;i++) total+=p[i];
    total+=value.item+value.npc_code;
    if((total&3)!=value.checksum) return 0;
    copy((u8 *)out,(const u8 *)&value,sizeof(value));return 1;
}
int af_v3_password_encode(const u8 *t,u32 size,const af_v3_password *v,u8 *text,u32 length) {
    u8 p[21],result[28];u32 i,bit,total,rate,npc_type,npc_code;
    if(!v||!text||length!=28||v->type>=6||!tables_ok(t,size)) return 0;
    rate=v->hit_rate_index;npc_type=v->npc_type;npc_code=v->npc_code;
    if(v->type==0||v->type==4||v->type==5) { rate=1;npc_code=255; }
    else if(v->type==1) rate=4; /* Preserve the source's popularity-code rule. */
    else if(v->type==3) { npc_type=(rate>>2)&1;rate&=3;npc_code=255; }
    if(rate>4) return 0;
    for(i=0;i<21;i++) p[i]=0;
    p[0]=(u8)((v->type<<5)|(rate<<1)|(npc_type&1));p[1]=(u8)npc_code;
    copy(p+2,v->str0,8);copy(p+10,v->str1,8);
    p[18]=(u8)(v->item>>8);p[19]=(u8)v->item;total=v->item+npc_code;
    for(i=2;i<18;i++) total+=p[i];
    p[0]|=(u8)((total&3)<<3);
    for(i=0;i<21;i++)p[i]=t[SUB+p[i]];
    transpose(p,t,0,-1);shuffle(p,t,0,0);if(!rsa(p,t,0))return 0;
    mix(p,0);shuffle(p,t,1,0);transpose(p,t,1,1);
    for(i=0;i<28;i++)result[i]=0;
    for(bit=0;bit<168;bit++)result[bit/6]|=(u8)(((p[bit/8]>>(bit%8))&1)<<(bit%6));
    for(i=0;i<28;i++) { result[i]=t[ALPH+result[i]];if(result[i]==209)result[i]='#'; }
    copy(text,result,28);return 1;
}
