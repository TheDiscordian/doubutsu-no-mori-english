#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/equipment_resources.c"
u32 af_equipment_native_pointers[17], af_equipment_native_bounds[18];
u8 af_equipment_native_types[17];
u32 af_equipment_header[2048];

#ifdef AF_V3_PLAYER_MOTION
u32 af_player_native_bounds[131],af_player_header[644];
u8 af_player_fan_mask[27];
static int native_part_calls;
void af_v3_native_player_part(u8 *out,int index) {
    ++native_part_calls;memset(out,0xF0+index,27);
}
static void player_tests(void) {
    for(int i=0;i<131;++i)player_bounds[i]=0x06000000+i*128;
    for(int i=0;i<130;++i) {
        assert(af_v3_player_animation_size(i)==120);
        assert(af_v3_player_animation_origin(i)==(u32)i*128+8);
        assert(af_v3_player_animation_vrom(i)==0x00B36000+(u32)i*128+8);
    }
    af_player_header[0]=0x4146504D;af_player_header[1]=1;
    af_player_header[2]=157;af_player_header[3]=16;
    Resource *rows=(Resource *)(af_player_header+4);
    rows[139]=(Resource){0x02500000,512,0x060001E0,4};
    assert(af_v3_player_animation_pointer(269)==0x060001E0);
    assert(af_v3_player_animation_part(269)==4);
    assert(af_v3_player_animation_size(269)==512 && !af_v3_player_animation_origin(269));
    assert(af_v3_player_animation_vrom(269)==0x02500000);
    int bad[]={-1,INT_MIN,INT_MAX,130,286,287};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) {
        int index=bad[i];
        assert(!af_v3_player_animation_pointer(index));assert(af_v3_player_animation_part(index)==-1);
        assert(!af_v3_player_animation_size(index));assert(!af_v3_player_animation_origin(index));
        assert(af_v3_player_animation_vrom(index)==0x00B36000);
    }
    for(int i=0;i<4;++i) {af_player_header[i]^=1;assert(!af_v3_player_animation_size(269));af_player_header[i]^=1;}
    Resource good=rows[139];
    for(int i=0;i<6;++i) {
        rows[139]=good;
        if(i==0)rows[139].bytes=16;
        if(i==1)rows[139].bytes=3856;
        if(i==2)rows[139].pointer=0x060001F0;
        if(i==3)rows[139].type=5;
        if(i==4)rows[139].vrom=0x025EFFF0;
        if(i==5)rows[139].vrom+=1;
        assert(!af_v3_player_animation_size(269));
    }
    rows[139]=good;
    for(int i=0;i<27;++i)af_player_fan_mask[i]=i&1;
    u8 out[29];memset(out,0xA5,sizeof(out));
    for(int i=0;i<4;++i) {
        af_v3_player_part_copy(out+1,i);assert(out[1]==0xF0+i && out[27]==0xF0+i);
    }
    assert(native_part_calls==4);
    af_v3_player_part_copy(out+1,4);assert(!memcmp(out+1,af_player_fan_mask,27));
    af_v3_player_part_copy(out+1,-1);af_v3_player_part_copy(out+1,5);
    assert(!memcmp(out+1,af_player_fan_mask,27) && out[0]==0xA5 && out[28]==0xA5);
    assert(native_part_calls==4);
}
#endif

static void invalid(int index) {
    assert(!af_v3_equipment_pointer(index));
    assert(!af_v3_equipment_type(index));
    assert(!af_v3_equipment_size(index));
    assert(!af_v3_equipment_origin(index));
    assert(af_v3_equipment_vrom(index)==0x00B8B000);
}
int main(void) {
    for (int i=0;i<18;++i) native_bounds[i]=0x06000000+i*128;
    for (int i=0;i<17;++i) {
        native_pointers[i]=0x06000010+i*128;native_types[i]=i%4;
        assert(af_v3_equipment_pointer(i)==native_pointers[i]);
        assert(af_v3_equipment_type(i)==native_types[i]);
        assert(af_v3_equipment_size(i)==120);
        assert(af_v3_equipment_origin(i)==(u32)i*128+8);
        assert(af_v3_equipment_vrom(i)==0x00B8B000+(u32)i*128+8);
    }
    invalid(-1);invalid(INT_MIN);invalid(INT_MAX);invalid(67);invalid(17);
    af_equipment_header[0]=0x41464852;af_equipment_header[1]=1;
    af_equipment_header[2]=50;af_equipment_header[3]=16;
    Resource *rows=(Resource *)(af_equipment_header+4);
    for (int type=0;type<=5;++type) {
        rows[49]=(Resource){0x02500000,32,0x06000008,type};
        if(type==1) { invalid(66);continue; }
        assert(af_v3_equipment_pointer(66)==0x06000008);
        assert(af_v3_equipment_type(66)==(u32)type);
        assert(af_v3_equipment_size(66)==32 && !af_v3_equipment_origin(66));
        assert(af_v3_equipment_vrom(66)==0x02500000);
    }
    invalid(17);invalid(65);
    const Resource good={0x02500000,32,0x06000008,2};
    const Resource bad[]={
        {0x021FFFF0,32,0x06000008,2},{0x025F0000,32,0x06000008,2},
        {0x025EFFF0,32,0x06000008,2},{0x02500001,32,0x06000008,2},
        {0x02500000,0,0x06000008,2},{0x02500000,16,0x06000008,2},
        {0x02500000,31,0x06000008,2},{0x02500000,4384,0x06000008,2},
        {0x02500000,32,0x05000008,2},{0x02500000,32,0x06000009,2},
        {0x02500000,32,0x06000010,2},{0x02500000,32,0x06000008,6},
    };
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) { rows[49]=bad[i];invalid(66); }
    rows[49]=good;
    for(int i=0;i<4;++i) {af_equipment_header[i]^=1;invalid(66);af_equipment_header[i]^=1;}
#ifdef AF_V3_PLAYER_MOTION
    player_tests();
#endif
    puts("pass: native fallback, shared static/motion readers, invalid indices and records");
}
