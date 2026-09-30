#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int u32;
typedef unsigned short u16;
struct Node { u16 magic, free; u32 size, next, previous; };
_Alignas(16) unsigned char af_scene_test_workspace[0x50000];
u32 af_scene_test_detected=0x800000, af_scene_test_title;
u32 af_scene_test_number=7, af_scene_test_borrowed;
static int init_calls, add_calls, cleanup_calls;
static jmp_buf rejected;
void af_v3_scene_init(void *,u32);
void af_v3_scene_cleanup(void);
void af_v3_save_halt(int error) { assert(error==-3); longjmp(rejected,1); }
void af_scene_native_init(void *base,u32 size) {
    assert(base==(void *)0x80200000u && size==0x100000u); ++init_calls;
}
void af_scene_native_add(void *arena,void *base,u32 size) {
    assert(arena==(void *)0x80141FA0u);
    if (add_calls==0) { assert(base==af_scene_test_workspace+16 && size==32); }
    else {
        assert(add_calls==1 && base==af_scene_test_workspace+48 && size==0x4FFC0);
        assert(((struct Node *)(af_scene_test_workspace+16))->free==0);
    }
    struct Node *n=base;
    *n=(struct Node){0x7373,1,size-16,0,0}; ++add_calls;
}
void af_scene_native_cleanup(void) { ++cleanup_calls; }
int main(void) {
    af_scene_test_detected=0x400000;
    if (!setjmp(rejected)) { af_v3_scene_init((void *)0x80200000u,0x100000); assert(0); }
    assert(init_calls==0);
    af_scene_test_detected=0x800000; af_scene_test_title=0x80400010;
    if (!setjmp(rejected)) { af_v3_scene_init((void *)0x80200000u,0x100000); assert(0); }
    assert(init_calls==0);
    af_scene_test_title=0;
    af_v3_scene_init((void *)0x80200000u,0x100000);
    assert(init_calls==1 && add_calls==2);
    assert(((struct Node *)(af_scene_test_workspace+48))->size==0x4FFB0);
    assert(af_scene_test_borrowed==1);
    if (!setjmp(rejected)) { af_v3_scene_init((void *)0x80200000u,0x100000); assert(0); }
    af_scene_test_workspace[0]^=1;
    if (!setjmp(rejected)) { af_v3_scene_cleanup(); assert(0); }
    assert(cleanup_calls==0); af_scene_test_workspace[0]^=1;
    af_scene_test_workspace[0x4FFF0]^=1;
    if (!setjmp(rejected)) { af_v3_scene_cleanup(); assert(0); }
    assert(cleanup_calls==0); af_scene_test_workspace[0x4FFF0]^=1;
    af_scene_test_title=0x80400010;
    if (!setjmp(rejected)) { af_v3_scene_cleanup(); assert(0); }
    assert(cleanup_calls==0);
    af_scene_test_title=0;
    af_v3_scene_cleanup(); assert(cleanup_calls==1 && af_scene_test_borrowed==0);
    af_scene_test_number=33;
    af_v3_scene_init((void *)0x80200000u,0x100000);
    assert(init_calls==2 && add_calls==2 && af_scene_test_borrowed==0);
    af_scene_test_title=0x80400010;
    af_scene_test_workspace[0]^=1;
    af_v3_scene_cleanup(); assert(cleanup_calls==2);
    puts("Exclusive scene ownership, cross-block sentinel, and guards pass");
}
