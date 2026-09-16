#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/equipment_resources.c"
u32 af_equipment_native_pointers[17], af_equipment_native_bounds[18];
u8 af_equipment_native_types[17];
u32 af_equipment_header[2048];

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
    puts("pass: native fallback, shared static/motion readers, invalid indices and records");
}
