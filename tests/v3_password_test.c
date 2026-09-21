/* Synthetic payloads; independent reference and actual tables stay in build/. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/password.c"
extern void ref_encode(const af_v3_password *,u8 *,unsigned *);
extern int ref_decode(const u8 *,af_v3_password *);
extern void ref_raw(const u8 *,u8 *);
static unsigned random_state=0x4121983;
static unsigned next(void) { random_state^=random_state<<13;random_state^=random_state>>17;
    random_state^=random_state<<5;return random_state; }
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    u8 data[2048],original[2048];size_t size=fread(data,1,sizeof(data),f);assert(feof(f));fclose(f);
    memcpy(original,data,size);assert(tables_ok(data,(u32)size));
    assert(sizeof(af_v3_password)==24);
    struct { u8 before[16];af_v3_password value;u8 after[16]; } guard;
    struct { u8 before[16],text[28],after[16]; } encoded;
    unsigned coverage[6]={0},valid[6]={0},invalid[6]={0},aliases=0;
    af_v3_password value,reference,untouched;u8 expected[28],input[28];
    memset(&untouched,0xA5,sizeof(untouched));
    for(unsigned type=0;type<6;type++) for(unsigned trial=0;trial<64;trial++) {
        memset(&value,0,sizeof(value));value.type=(u8)type;value.item=(af_pw_u16)next();
        value.hit_rate_index=(u8)(trial%4);if(type==3)value.hit_rate_index=(u8)(trial%5);
        value.npc_type=(u8)(trial&1);value.npc_code=(u8)next();
        for(unsigned i=0;i<8;i++) { value.str0[i]=(u8)next();value.str1[i]=(u8)next(); }
        af_v3_password saved=value;
        memset(&encoded,0xA5,sizeof(encoded));ref_encode(&value,expected,coverage);
        assert(af_v3_password_encode(data,(u32)size,&value,encoded.text,28));
        assert(!memcmp(&value,&saved,sizeof(value)) && !memcmp(expected,encoded.text,28));
        memset(&guard,0xA5,sizeof(guard));
        int wanted=ref_decode(expected,&reference);
        assert(af_v3_password_decode(data,(u32)size,encoded.text,28,&guard.value)==wanted);
        assert(!memcmp(expected,encoded.text,28));
        if(wanted) { assert(!memcmp(&reference,&guard.value,sizeof(reference)));valid[type]++; }
        else { assert(!memcmp(&guard.value,&untouched,sizeof(untouched)));invalid[type]++; }
        for(unsigned i=0;i<16;i++) assert(guard.before[i]==0xA5 && guard.after[i]==0xA5
            && encoded.before[i]==0xA5 && encoded.after[i]==0xA5);
        memcpy(input,expected,28);
        for(unsigned i=0;i<28;i++) {
            if(input[i]=='O') { input[i]='0';aliases|=1; }
            if(input[i]=='l') { input[i]='1';aliases|=2; }
            if(input[i]=='#') { input[i]=209;aliases|=4; }
        }
        guard.value=untouched;
        assert(af_v3_password_decode(data,(u32)size,input,28,&guard.value)==wanted);
        assert(!memcmp(&guard.value,wanted?&reference:&untouched,sizeof(reference)));
    }
    assert(aliases==7);
    for(unsigned i=0;i<6;i++) {
        assert(coverage[i]==((i==1||i==4)?15u:65535u));assert(valid[i]);
        if(i!=1)assert(!invalid[i]);
    }
    /* Source's popular-code encoder overlaps checksum; retain that behaviour. */
    assert(invalid[1]);
    memset(&guard,0xA5,sizeof(guard));memset(&encoded,0xA5,sizeof(encoded));
    for(unsigned n=0;n<28;n++) {
        assert(!af_v3_password_decode(data,(u32)size,input,n,&guard.value));
        assert(!af_v3_password_encode(data,(u32)size,&value,encoded.text,n));
    }
    assert(!af_v3_password_decode(data,(u32)size,input,29,&guard.value));
    assert(!af_v3_password_decode(data,(u32)size,NULL,28,&guard.value));
    assert(!af_v3_password_decode(data,(u32)size,input,28,NULL));
    assert(!af_v3_password_encode(data,(u32)size,NULL,encoded.text,28));
    assert(!af_v3_password_encode(data,(u32)size,&value,NULL,28));
    value.type=6;assert(!af_v3_password_encode(data,(u32)size,&value,encoded.text,28));
    for(unsigned n=0;n<28;n++) {
        memcpy(input,expected,28);input[n]='!';
        assert(!af_v3_password_decode(data,(u32)size,input,28,&guard.value));
    }
    u8 raw[20]={0};raw[1]=255;
    for(unsigned bad_type=6;bad_type<8;bad_type++) {
        raw[0]=(u8)((bad_type<<5)|24);ref_raw(raw,input);
        assert(!ref_decode(input,&reference));
        assert(!af_v3_password_decode(data,(u32)size,input,28,&guard.value));
    }
    raw[0]=4<<5;ref_raw(raw,input); /* checksum zero should be three */
    assert(!ref_decode(input,&reference));
    assert(!af_v3_password_decode(data,(u32)size,input,28,&guard.value));
    assert(!memcmp(&guard.value,&untouched,sizeof(untouched)));
    for(unsigned i=0;i<sizeof(encoded);i++)assert(((u8 *)&encoded)[i]==0xA5);
    assert(!memcmp(data,original,size));
    for(unsigned n=0;n<size;n++)assert(!tables_ok(data,n));
    assert(!tables_ok(NULL,(u32)size));assert(!tables_ok(data,(u32)size+1));
    const unsigned bad_offsets[]={0,4,6,8,10,12,14,16,18,20,352,864,992,995};
    for(unsigned i=0;i<sizeof(bad_offsets)/sizeof(bad_offsets[0]);i++) {
        memcpy(data,original,size);data[bad_offsets[i]]=255;
        assert(!tables_ok(data,(u32)size));
        assert(!af_v3_password_decode(data,(u32)size,expected,28,&guard.value));
    }
    memcpy(data,original,size);data[97]=data[96];assert(!tables_ok(data,(u32)size));
    memcpy(data,original,size);data[33]=data[32];assert(!tables_ok(data,(u32)size));
    memcpy(data,original,size);data[865]=data[864];assert(!tables_ok(data,(u32)size));
    assert(!memcmp(&guard.value,&untouched,sizeof(untouched)));
    puts("All six types, donor agreement, aliases, and transactional bounds pass (384 payloads)");
    return 0;
}
