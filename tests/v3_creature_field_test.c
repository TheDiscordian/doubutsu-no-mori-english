#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#define AF_FIELD_POOL_ROM 0x3E00000u
#define AF_FIELD_POOL_BYTES (17u*16u)
#include "../overlays/v3/creature_field.c"
static unsigned char records[16+17*24],pool[AF_FIELD_POOL_BYTES];
const u8 *af_test_field_metadata=records;
static jmp_buf fault;
static unsigned dma_calls,pi_calls,fail_pi;
static _Alignas(16) unsigned char destination[0xC10];
static _Alignas(16) unsigned char actor[0x280];
static char rotations[8];
static short angles[8];
static unsigned matrix_calls;
void af_field_scale(float x,float y,float z,int mode) {
    assert(x==1 && y==2 && z==3 && mode==1);rotations[matrix_calls++]='S';
}
void af_field_rotate_x(short angle,int mode) {assert(mode==1);angles[matrix_calls]=angle;rotations[matrix_calls++]='X';}
void af_field_rotate_y(short angle,int mode) {assert(mode==1);angles[matrix_calls]=angle;rotations[matrix_calls++]='Y';}
void af_field_rotate_z(short angle,int mode) {assert(mode==1);angles[matrix_calls]=angle;rotations[matrix_calls++]='Z';}
static void put(unsigned char *p,unsigned value) {
    p[0]=value>>24;p[1]=value>>16;p[2]=value>>8;p[3]=value;
}
u32 af_field_crc(const void *p,u32 n) {
    const u8 *data=p;u32 crc=0xFFFFFFFFu;
    for(u32 i=0;i<n;i++) {
        crc^=data[i];
        for(u32 bit=0;bit<8;bit++)crc=(crc>>1)^((0u-(crc&1))&0xEDB88320u);
    }
    return ~crc;
}
int af_field_pi(u32 physical,void *out,u32 n) {
    assert(physical>=AF_FIELD_POOL_ROM && physical-AF_FIELD_POOL_ROM+n<=sizeof(pool));
    assert(out==destination && n==16);pi_calls++;
    if(fail_pi)return -1;
    memcpy(out,pool+physical-AF_FIELD_POOL_ROM,n);return 0;
}
int af_field_dma(void *out,u32 vrom,u32 n,const char *file,int line) {
    assert(out==destination && n==16 && !strcmp(file,"native") && line==123);
    assert(vrom==0x1871008 || vrom==0x113D008);dma_calls++;return 7;
}
void af_field_fault(const char *title,const char *reason) {
    assert(!strcmp(title,"Creature graphics") && reason);longjmp(fault,1);
}
static void rejects(u32 address,u32 bytes,void *out) {
    if(!setjmp(fault)) {
        af_v3_creature_graphics_load(out,address,bytes,"test",0);assert(0);
    }
}
int main(void) {
    memset(destination,0xA5,sizeof(destination));
    put(records,0x41464346);put(records+4,1);put(records+8,17);put(records+12,24);
    for(unsigned i=0;i<17;i++) {
        unsigned char *r=records+16+i*24;
        memset(pool+i*16,i+1,16);
        put(r,0x1880000+i*16);put(r+4,16);put(r+8,i*16);
        put(r+12,af_field_crc(pool+i*16,16));put(r+16,0xA00);put(r+20,0x2320+i);
    }
    assert(af_v3_creature_graphics_load(destination,0x1871008,16,"native",123)==7);
    assert(af_v3_creature_graphics_load(destination,0x113D008,16,"native",123)==7);
    for(unsigned i=0;i<17;i++) {
        assert(!af_v3_creature_graphics_load(destination,0x1880000+i*16,16,"test",0));
        assert(!memcmp(destination,pool+i*16,16) && destination[16]==0xA5);
    }
    assert(dma_calls==2 && pi_calls==17);
    rejects(0x1880000,32,destination);rejects(0x1880001,16,destination);
    rejects(0x1880000,16,destination+1);rejects(0x1880000,16,0);
    rejects(0x187FF98,16,destination);rejects(0x1146948,16,destination);
    put(records+16+8,sizeof(pool));rejects(0x1880000,16,destination);put(records+16+8,0);
    put(records+16+16,8);rejects(0x1880000,16,destination);put(records+16+16,0xA00);
    records[16+12]^=1;rejects(0x1880000,16,destination);records[16+12]^=1;
    fail_pi=1;rejects(0x1880000,16,destination);fail_pi=0;
    records[0]^=1;rejects(0x1880000,16,destination);records[0]^=1;
    assert(dma_calls==2);
    ((float *)(actor+0x5C))[0]=1;((float *)(actor+0x5C))[1]=2;((float *)(actor+0x5C))[2]=3;
    *(short *)(actor+0xDC)=123;*(short *)(actor+0xDE)=456;*(short *)(actor+0xE0)=789;
    for(int species=0;species<40;species++)for(int held=0;held<2;held++)for(int frame=0;frame<4;frame++) {
        *(int *)(actor+0x1CC)=species;*(int *)(actor+0x1B8)=held;matrix_calls=0;
        af_v3_creature_insect_transform(actor,frame);
        if(species<32) {
            assert(matrix_calls==3 && !memcmp(rotations,"SXY",3));
            short x=123,y=456;
            if(held) {
                x=y=0;
                if(species==13 || species==14 || species==16)y=-0x4000;
                else if(species!=27){x=0x2000;y=(short)0x8000;}
            }
            assert(angles[1]==x && angles[2]==y);
        } else if(held) {
            assert(matrix_calls==3 && !memcmp(rotations,"XYS",3));
            assert(angles[0]==0x4000 && angles[1]==(species==37 ? 0 : (short)0x8000));
        } else if(species==33)assert(matrix_calls==4 && !memcmp(rotations,"YXZS",4));
        else if(species==37 && frame==2)assert(matrix_calls==3 && !memcmp(rotations,"XZS",3));
        else assert(matrix_calls==4 && !memcmp(rotations,"XYZS",4));
    }
    puts("Complete creature PI loading, native fallback, bounds, and CRC failures: pass");
}
