#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "../overlays/v3/room_rigs.h"

static void entry2(RoomRig *,u8 *);
static void entry4(RoomRig *,void *,RoomRigGame *,u8 *);
static void move_sound(u32,float *);
#define AF_ROOM_RAM 0x804D0000u
#define AF_ROOM_BYTES 36864u
#define AF_ROOM_VROM 0x02300000u
#define AF_ROOM_CRC 0x12345678u
#define AF_ROOM_CT entry2
#define AF_ROOM_DT entry2
#define AF_ROOM_MV entry4
#define AF_ROOM_DW entry4
#define AF_ROOM_SOUND_MV entry4
#define AF_ROOM_MATERIAL_DW entry4
#define AF_ROOM_SCROLL_CT entry2
#define AF_ROOM_SCROLL_DT entry2
#define AF_ROOM_SCROLL_MV entry4
#define AF_ROOM_SCROLL_DW entry4
#define AF_ROOM_SCROLL_MOVE_SOUND move_sound
#define AF_ROOM_SCROLL_BYTES 8192u
#define AF_ROOM_SCROLL_VROM 0x02310000u
#define AF_ROOM_SCROLL_CRC 0x87654321u
#define AF_ROOM_EFFECTS
#define AF_ROOM_REACTIONS
#define AF_ROOM_COLOURS
#include "../overlays/v3/room_rigs_bootstrap.c"

static unsigned dma_count,crc_count,writebacks,invalidates,faults,calls;
static unsigned fail_dma,fail_crc,scroll_expected;
static RoomRig actor;
static RoomRigGame game;
static int owner;
static u8 object;
static void *packet;
static u32 bytes;
int af_room_dma(void *p,u32 vrom,u32 n) {
    ++dma_count;assert(p==(void *)(uptr)(scroll_expected ? 0x804BA000u : AF_ROOM_RAM));
    assert(vrom==(scroll_expected ? AF_ROOM_SCROLL_VROM : AF_ROOM_VROM));
    assert(n==(scroll_expected ? AF_ROOM_SCROLL_BYTES : AF_ROOM_BYTES));packet=p;bytes=n;return (int)fail_dma;
}
u32 af_room_crc(void *p,u32 n) {
    ++crc_count;assert(p==packet && n==bytes);return fail_crc ? 0 : scroll_expected ? AF_ROOM_SCROLL_CRC : AF_ROOM_CRC;
}
void af_room_writeback(void *p,u32 n) {assert(p==packet && n==bytes);++writebacks;}
void af_room_invalidate(void *p,u32 n) {assert(p==packet && n==bytes && writebacks==invalidates+1);++invalidates;}
void af_room_fault(const char *title,const char *message) {
    assert(!strcmp(title,scroll_expected ? "V3 room materials" : "V3 room rigs"));
    assert(!strcmp(message,scroll_expected ? "Invalid scroll code" : "Invalid room code"));++faults;
}
static void entered(void) {
    volatile u32 *ready=(void *)(uptr)(scroll_expected ? 0x804B1E04u : 0x804B1E00u);
    assert(*ready==(scroll_expected ? AF_ROOM_SCROLL_CRC : AF_ROOM_CRC));assert(writebacks==invalidates);++calls;
}
static void entry2(RoomRig *a,u8 *data) {assert(a==&actor && data==&object);entered();}
static void entry4(RoomRig *a,void *room,RoomRigGame *g,u8 *data) {
    assert(a==&actor && room==&owner && g==&game && data==&object);entered();
}
static void move_sound(u32 floor,float *position) {assert(floor==13 && position==actor.position);entered();}
static void invoke(unsigned n) {
    switch(n) {
        case 0:af_v3_room_boot_ct(&actor,&object);break;
        case 1:af_v3_room_boot_dt(&actor,&object);break;
        case 2:af_v3_room_boot_mv(&actor,&owner,&game,&object);break;
        case 3:af_v3_room_boot_dw(&actor,&owner,&game,&object);break;
        case 4:af_v3_room_boot_sound_mv(&actor,&owner,&game,&object);break;
        case 5:af_v3_room_boot_material_dw(&actor,&owner,&game,&object);break;
        case 6:af_v3_room_boot_scroll_ct(&actor,&object);break;
        case 7:af_v3_room_boot_scroll_dt(&actor,&object);break;
        case 8:af_v3_room_boot_scroll_mv(&actor,&owner,&game,&object);break;
        case 9:af_v3_room_boot_scroll_dw(&actor,&owner,&game,&object);break;
        case 10:af_v3_room_boot_scroll_move_sound(13,actor.position);break;
        default:assert(0);
    }
}
int main(void) {
    assert(mmap((void *)0x804B1000u,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x804B1000u);
    assert(mmap((void *)0x804CD000u,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x804CD000u);
    volatile u32 *reaction=(void *)ROOM_REACTION_STATE_RAM,*colour=(void *)ROOM_COLOUR_RAM;
    for (unsigned n=0;n<11;++n) {
        scroll_expected=n>=6;volatile u32 *ready=(void *)(uptr)(scroll_expected ? 0x804B1E04u : 0x804B1E00u);
        for (unsigned failure=0;failure<3;++failure) {
            *ready=0;*reaction=77;*colour=88;fail_dma=failure==1;fail_crc=failure==2;
            unsigned c=calls,d=dma_count,f=faults,w=writebacks,h=crc_count;invoke(n);
            assert(dma_count==d+1 && crc_count==h+(failure!=1));
            if (failure) {
                assert(calls==c && faults==f+1 && writebacks==w && !*ready && *reaction==77 && *colour==88);
            } else {
                assert(calls==c+1 && faults==f && writebacks==w+1);
                assert(*reaction==(scroll_expected ? 77u : 0u) && *colour==(scroll_expected ? 88u : 0u));
                *reaction=99;*colour=100;invoke(n);
                assert(calls==c+2 && dma_count==d+1 && writebacks==w+1 && *reaction==99 && *colour==100);
            }
        }
    }
    assert(munmap((void *)0x804B1000u,4096)==0 && munmap((void *)0x804CD000u,4096)==0);
    puts("11 bootstrap entries preserve arguments, cold/warm checks, failure rejection, state reset, and cache ordering");
}
