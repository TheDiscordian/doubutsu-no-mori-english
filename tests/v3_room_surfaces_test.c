#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_SURFACE_FLOOR_VROM 0x025F0000u
#define AF_SURFACE_WALL_VROM 0x025FA0A0u
#include "../overlays/v3/room_surfaces.c"

static unsigned calls;
static u32 expected_address,expected_size;
static unsigned char buffers[4][0x2040];
int af_surface_dma(void *destination,u32 address,u32 size) {
    assert(address==expected_address && size==expected_size);
    int found=0;
    for (unsigned i=0;i<4;i++) if (destination==buffers[i]+16) found=1;
    assert(found);
    memset(destination,0xC7,size);calls++;
    return 0;
}
static void reset(void) {memset(buffers,0xA5,sizeof(buffers));calls=0;}
static void check(unsigned index,int touched,u32 bytes) {
    for (unsigned j=0;j<sizeof(buffers[0]);j++)
        assert(buffers[index][j]==(touched && j>=16 && j<16+bytes ? 0xC7 : 0xA5));
}
int main(void) {
    SurfaceRoom room;
    memset(&room,0x65,sizeof(room));
    room.floor[0]=buffers[0]+16;room.floor[1]=buffers[1]+16;
    room.wall[0]=buffers[2]+16;room.wall[1]=buffers[3]+16;
    SurfaceRoom original=room;
    const short indices[]={0,26,63,64,67,73,74,75,76,77};
    for (unsigned wall=0;wall<2;wall++) {
        void (*copy)(SurfaceRoom *,int,int)=wall ? af_v3_surface_wall : af_v3_surface_floor;
        expected_size=wall ? 0x1020u : 0x2020u;
        for (unsigned n=0;n<sizeof(indices)/sizeof(indices[0]);n++) {
            short index=indices[n];
            expected_address=index<68 ? (wall ? 0x0182A000u : 0x017A1000u)+index*expected_size
                : (wall ? AF_SURFACE_WALL_VROM : AF_SURFACE_FLOOR_VROM)+(index-73)*expected_size;
            for (short bank=0;bank<3;bank++) {
                reset();copy(&room,index,bank);assert(calls==(bank==2 ? 2u : 1u));
                for (unsigned i=0;i<4;i++) check(i,i/2==wall && (bank==2 || i%2==(unsigned)bank),expected_size);
                assert(!memcmp(&room,&original,sizeof(room)));
            }
        }
        const short invalid[]={-32768,-1,68,69,70,71,72,78,127,255,32767};
        for (unsigned n=0;n<sizeof(invalid)/sizeof(invalid[0]);n++) {reset();copy(&room,invalid[n],2);assert(!calls);}
        for (short bank=-1;bank<5;bank+=4) {reset();copy(&room,73,bank);assert(!calls);}
        reset();copy(NULL,73,2);assert(!calls);
        expected_address=wall ? AF_SURFACE_WALL_VROM : AF_SURFACE_FLOOR_VROM;
        reset();copy(&room,0x12340049,0x56780002);assert(calls==2);
        SurfaceRoom sparse=room;(wall ? sparse.wall : sparse.floor)[0]=NULL;
        reset();copy(&sparse,73,2);assert(calls==1);check(wall*2,0,expected_size);check(wall*2+1,1,expected_size);
    }
    assert(!memcmp(&room,&original,sizeof(room)));
    puts("surface routing, double buffers, missing IDs, nulls, guards, and unchanged actor state pass");
    return 0;
}
