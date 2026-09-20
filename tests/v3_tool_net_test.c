#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/tool_net.c"

static union { int align; unsigned char bytes[0x13A0]; } actor;
static int actual_kind, kind_calls, force_calls;
static int force(void *p, u32 *label, signed char *type) {
    assert(p == actor.bytes); ++force_calls;
    u32 forced=*(u32 *)(actor.bytes+0xF1C);
    if (!forced) return 0;
    *label=forced; *type=(signed char)actor.bytes[0xF20]; return 1;
}
static int kind(void) { ++kind_calls; return actual_kind; }
void *af_test_net_function(u32 at) {
    if (at==0x808CC7B4u) return force;
    if (at==0x808BD3F8u) return kind;
    assert(0); return 0;
}
int main(void) {
    const int counts[]={INT_MIN,-1,0,1,8,9,INT_MAX};
    const int kinds[]={INT_MIN,-1,0,1,44,45,46,47,88,90,114,INT_MAX};
    for (unsigned n=0;n<sizeof(counts)/sizeof(*counts);++n)
    for (unsigned k=0;k<sizeof(kinds)/sizeof(*kinds);++k)
    for (int forced=0;forced<2;++forced) {
        memset(actor.bytes,0xA5,sizeof(actor.bytes));
        *(int *)(actor.bytes+0xF18)=counts[n];
        *(u32 *)(actor.bytes+0xF1C)=forced ? 0x87654321u : 0;
        actor.bytes[0xF20]=0xFE;
        unsigned char before[sizeof(actor.bytes)];memcpy(before,actor.bytes,sizeof(before));
        u32 values[]={0xDEADBEEFu,0xDEADBEEFu,0xDEADBEEFu,0xDEADBEEFu};
        u32 label=0xABCDEF01u;signed char type=11;
        actual_kind=kinds[k];kind_calls=force_calls=0;
        int result=af_v3_net_parameters(actor.bytes,&label,&type,values+1);
        assert(result==forced && force_calls==1);
        int valid=!forced && counts[n]>0 && counts[n]<=8;
        assert(kind_calls==valid);
        assert(label==(forced ? 0x87654321u : 0xABCDEF01u) && type==(forced ? -2 : 11));
        assert(values[0]==0xDEADBEEFu && values[3]==0xDEADBEEFu);
        if (valid) {
            float radius,span;memcpy(&radius,values+1,4);memcpy(&span,values+2,4);
            assert(radius==(actual_kind==46 ? 21.0f : 15.0f));
            assert(span==(actual_kind==46 ? 60.0f : 50.0f));
        } else assert(values[1]==0xDEADBEEFu && values[2]==0xDEADBEEFu);
        assert(memcmp(before,actor.bytes,sizeof(before))==0);
    }
    puts("Native forced priority, bounded counts, real kind, dimensions, and immutable state pass");
    return 0;
}
