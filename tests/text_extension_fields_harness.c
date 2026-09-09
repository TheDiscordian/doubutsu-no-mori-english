#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "extension.h"

static unsigned char window[1024], other[1024];
static _Alignas(16) unsigned char msg[16+1024+16];
static unsigned int instructions[0x30000/4], writes, invalidates;
static int forced_size = 2;

void *af_free_test_window(void) { return window; }
unsigned char *af_free_test_message(void *value) { return value == window ? msg : 0; }
af_u32 *af_free_test_code(af_u32 address) {
    assert(address >= 0x80090000u && address < 0x800C0000u && !(address & 3));
    return &instructions[(address-0x80090000u)/4];
}
void af_writeback(void *address, unsigned int length) { (void)address; assert(length == 8); ++writes; }
void af_invalidate(void *address, unsigned int length) { (void)address; assert(length == 8); ++invalidates; }
int af_native_code_size(unsigned char *data, int index) { (void)data; (void)index; return forced_size; }
int af_native_move(unsigned char *data, int to, int from, int length, int flags) {
    assert(flags == 0 && from >= 0 && from <= length && to >= 0 && length+to-from <= 1024);
    memmove(data+to, data+from, (unsigned int)(length-from));
    return length+to-from;
}
void af_native_copy(unsigned char *destination, const unsigned char *source, int length) {
    assert(length >= 0 && length <= 16);
    if (length) memcpy(destination,source,(unsigned int)length);
}
int af_load_item_name(unsigned char *destination, unsigned int capacity, unsigned int item) {
    assert(capacity == 16);
    if (item == 0xffffu) return 0;
    memcpy(destination, item ? "abcdefghijklmnop" : "                ",16);
    return 1;
}

static void native_entries(void) {
    memset(instructions,0,sizeof(instructions));
    *af_free_test_code(0x800A1370)=0x0C027C8C;
    *af_free_test_code(0x800A1394)=0x27BDFFD8;
    *af_free_test_code(0x800BB6F0)=0x27BDFFD8;
    *af_free_test_code(0x800BB6F4)=0xAFBF0014;
    writes=invalidates=0;
}

static void check_field(void *value, int slot, const char *expected, int size) {
    unsigned char data[1040], original[1040];
    memset(data,0xAB,sizeof(data));
    data[0]='A'; data[1]=0x7f; data[2]=0x1e; data[3]='Z';
    memcpy(original,data,sizeof(data));
    assert(af_free_copy(value,slot,data,1,4) == size+2);
    assert(data[0] == 'A' && data[size+1] == 'Z');
    assert(memcmp(data+1,expected,(unsigned int)size) == 0);
    /* Shrinking a message does not erase the abandoned original bytes. */
    for (int i=size+2; i<(int)sizeof(data); ++i) assert(data[i] == original[i]);
}

int main(void) {
    static const char full[]="abcdefghijklmnop";
    unsigned char before[1024];
    native_entries();
    *af_free_test_code(0x800A1394)^=1;
    assert(af_text_extension_init() == 0 && writes == 0 && invalidates == 0);
    native_entries();
    assert(af_text_extension_init() == 1 && writes == 6 && invalidates == 6);
    assert((*af_free_test_code(0x800A1370) >> 26) == 3);
    assert((*af_free_test_code(0x8009D6D0) >> 26) == 2);
    memset(window,' ',sizeof(window)); memset(other,' ',sizeof(other));
    for (int slot=0; slot<20; ++slot) {
        af_free_set(window,slot,(const unsigned char *)full,16);
        assert(memcmp(window+0x38+slot*10,full,10) == 0);
        check_field(window,slot,full,16);
        af_free_set(window,slot,(const unsigned char *)"short",5);
        check_field(window,slot,"short",5);
        af_free_set(window,slot,(const unsigned char *)"",0);
        check_field(window,slot,"",0);
    }
    af_free_set(window,0,(const unsigned char *)full,16);
    assert(af_text_extension_init() == 0); /* A failed repeat cannot clear valid rows. */
    check_field(window,0,full,16);
    af_free_set(window,0,window+0x38,10);
    check_field(window,0,full,10);
    af_free_set(window,0,(const unsigned char *)full,16);
    memcpy(before,window,sizeof(before));
    af_free_set(window,-1,(const unsigned char *)full,16);
    af_free_set(window,20,(const unsigned char *)full,16);
    af_free_set(window,0,(const unsigned char *)full,17);
    af_free_set(window,0,0,16);
    af_free_set(0,0,(const unsigned char *)full,16);
    assert(memcmp(before,window,sizeof(window)) == 0);
    check_field(window,-1,full,16); check_field(window,20,full,16);
    af_free_set(other,0,(const unsigned char *)full,10);
    af_free_set(other,0,(const unsigned char *)full,16);
    check_field(other,0,full,10);
    for (int slot=1; slot<=5; ++slot) {
        int offset=slot == 1 ? 0x280 : slot == 2 ? 0x281 : slot == 5 ? 0x282 : 0;
        if (!offset) continue;
        window[offset]=4;
        af_free_set(window,slot,0,0);
        assert(window[offset] == 0);
    }
    af_free_item(0x1234,0); check_field(window,0,full,16);
    af_free_item_nonzero(0,0); check_field(window,0,full,16);
    af_free_item(0xffff,0); check_field(window,0,full,16);
    af_free_item(0,0); check_field(window,0,"",0);
    af_free_item_colour(0x1234,2,2);
    assert(window[0x281] == 2);
    check_field(window,2,full,16);
    for (int colour=0; colour<5; ++colour) {
        int index=1, prefix=colour ? 6 : 0;
        memset(msg,0xAB,sizeof(msg));
        *(int *)(msg+8)=4;
        msg[16]='A'; msg[17]=0x7f; msg[18]=0x20; msg[19]='Z';
        assert(af_free_colour(window,&index,2,colour) == 0);
        assert(index == 1+prefix && *(int *)(msg+8) == 18+prefix);
        assert(memcmp(msg+17+prefix,full,16) == 0);
        if (colour) assert(msg[17] == 0x7f && msg[18] == 0x50 && msg[22] == 16);
        for (int i=16+18+prefix; i<(int)sizeof(msg); ++i) assert(msg[i] == 0xAB);
    }
    for (int colour=0; colour<2; ++colour) {
        int prefix=colour ? 6 : 0, length=1024-(16-2)-prefix, index=0;
        memset(msg,0xAB,sizeof(msg)); *(int *)(msg+8)=length;
        msg[16]=0x7f; msg[17]=0x20;
        af_free_colour(window,&index,2,colour);
        assert(*(int *)(msg+8) == 1024 && index == prefix);
        for (int i=1040; i<(int)sizeof(msg); ++i) assert(msg[i] == 0xAB);
        memset(msg,0xAB,sizeof(msg)); *(int *)(msg+8)=length+1;
        msg[16]=0x7f; msg[17]=0x20; index=0;
        memcpy(before,msg+16,1024);
        af_free_colour(window,&index,2,colour);
        assert(*(int *)(msg+8) == length+1 && index == 0 && memcmp(before,msg+16,1024) == 0);
    }
    forced_size=0;
    memset(msg,0xAB,sizeof(msg)); *(int *)(msg+8)=4;
    int index=0;
    af_free_colour(window,&index,2,2);
    assert(*(int *)(msg+8) == 4 && index == 0 && msg[16] == 0xAB);
    puts("Full free fields, native flags, complete colours, item bridges, and message bounds pass");
    return 0;
}
