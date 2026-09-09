#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "extension.h"

int af_choice_expand(unsigned char *, int, const unsigned char *);
static unsigned char window[1024];
static struct { af_u32 address, value; } code[64];
static unsigned int code_count, flushes, invalidates, legacy_calls;
static int selected_length=20, recursive;
static const unsigned char actor[8]={0};

af_u32 *af_choice_test_word(af_u32 address) {
    for (unsigned int i=0; i<code_count; ++i) if (code[i].address == address) return &code[i].value;
    assert(code_count < 64);
    code[code_count].address=address;
    return &code[code_count++].value;
}
af_u32 *af_free_test_code(af_u32 address) { return af_choice_test_word(address); }
void *af_choice_test_window(void) { return window; }
void *af_free_test_window(void) { return window; }
unsigned char *af_free_test_message(void *value) { (void)value; return 0; }
void af_writeback(void *address, unsigned int size) { (void)address; assert(size==8); ++flushes; }
void af_invalidate(void *address, unsigned int size) { (void)address; assert(size==8); ++invalidates; }
int af_native_code_size(unsigned char *data, int at) { assert(data[at]==0x7f); return 2; }
int af_native_move(unsigned char *data, int to, int from, int length, int flags) {
    assert(flags==0 && from<=length && to>=0 && length+to-from<=32);
    memmove(data+to,data+from,(unsigned int)(length-from)); return length+to-from;
}
void af_native_copy(unsigned char *to, const unsigned char *from, int size) {
    if (size) memcpy(to,from,(unsigned int)size);
}
int af_load_item_name(unsigned char *to, unsigned int capacity, unsigned int item) {
    assert(capacity==16); memset(to,item?'I':' ',16); return 1;
}
int af_copy_item_string(void *value, int slot, unsigned char *data, int at, int length) {
    assert(value==window && slot>=0 && slot<5 && at==0 && length==2);
    memset(data,recursive?0x7f:'I',16); return 16;
}
int af_copy_talk_name(const unsigned char *value, unsigned char *data, int at, int length) {
    assert(at==0 && length==2); if (!value) return 0;
    assert(value==actor); memcpy(data,"LongName",8); return 8;
}
int af_copy_catchphrase(const unsigned char *value, unsigned char *data, int at, int length) {
    assert(at==0 && length==2); if (!value) return 0;
    assert(value==actor); memcpy(data,"catch word",10); return 10;
}
int af_choice_test_selected(unsigned char *data) { memset(data,'S',(unsigned int)selected_length); return selected_length; }
int af_choice_test_legacy(unsigned int command, unsigned char *data, const unsigned char *value) {
    assert(value==actor); ++legacy_calls;
    assert(command==0x1a || (command>=0x1d && command<=0x23) || command==0x2f || command==0x30);
    memcpy(data,"legacy",6); return 6;
}

static void check(const unsigned char *source, int size, const unsigned char *expected, int result) {
    unsigned char guarded[52], before[52];
    memset(guarded,'!',sizeof(guarded)); memset(guarded+16,' ',20);
    memcpy(guarded+16,source,(unsigned int)size); memcpy(before,guarded,sizeof(before));
    int actual=af_choice_expand(guarded+16,20,actor);
    if (actual!=result) {
        fprintf(stderr,"choice result %d, expected %d; source:",actual,result);
        for (int i=0; i<size; ++i) fprintf(stderr," %02x",source[i]);
        fputc('\n',stderr);
    }
    assert(actual==result);
    assert(!memcmp(guarded,before,16) && !memcmp(guarded+36,before+36,16));
    if (!expected) assert(!memcmp(guarded,before,sizeof(before)));
    else {
        assert(!memcmp(guarded+16,expected,(unsigned int)result));
        for (int i=result; i<20; ++i) assert(guarded[16+i]==' ');
    }
}

int main(void) {
    *af_choice_test_word(0x80065cf8)=0x27bdffd0;
    *af_choice_test_word(0x80065cfc)=0xafb50028;
    *af_choice_test_word(0x80194908)=20; *af_choice_test_word(0x8019490c)=32;
    *af_choice_test_word(0x80194910)=0x8019a840; *af_choice_test_word(0x80194914)=0x8019a8c0;
    assert(af_text_extension_init()==0 && flushes==0);
    *af_choice_test_word(0x800A1370)=0x0c027c8c;
    *af_choice_test_word(0x800A1394)=0x27bdffd8;
    *af_choice_test_word(0x800BB6F0)=0x27bdffd8;
    *af_choice_test_word(0x800BB6F4)=0xafbf0014;
    assert(af_text_extension_init()==1 && flushes==7 && invalidates==7);
    assert(af_text_extension_init()==0 && flushes==7);
    for (int slot=0; slot<20; ++slot) {
        unsigned char source[]={'>',0x7f,(unsigned char)(slot<10?0x24+slot:0x36+slot-10),'!'};
        af_free_set(window,slot,(const unsigned char *)"abcdefghijklmnop",16);
        check(source,4,(const unsigned char *)">abcdefghijklmnop!",18);
    }
    for (int slot=0; slot<5; ++slot) {
        unsigned char source[]={0x7f,(unsigned char)(0x31+slot)};
        check(source,2,(const unsigned char *)"IIIIIIIIIIIIIIII",16);
    }
    check((const unsigned char *)"\x7f\x1b \x7f\x1c",5,(const unsigned char *)"LongName catch word",19);
    check((const unsigned char *)"\x7f\x2e",2,(const unsigned char *)"SSSSSSSSSSSSSSSSSSSS",20);
    selected_length=21; check((const unsigned char *)"\x7f\x2e",2,0,0); selected_length=20;
    for (int cmd=0x1a; cmd<=0x30; ++cmd) {
        if (!(cmd==0x1a || (cmd>=0x1d && cmd<=0x23) || cmd==0x2f || cmd==0x30)) continue;
        unsigned char source[]={0x7f,(unsigned char)cmd};
        check(source,2,(const unsigned char *)"legacy",6);
    }
    af_free_set(window,0,(const unsigned char *)"",0);
    check((const unsigned char *)"\x7f\x24 suffix",9,(const unsigned char *)" suffix",7);
    check((const unsigned char *)"plain  spaced       ",20,(const unsigned char *)"plain  spaced       ",20);
    check((const unsigned char *)"1234567890123456789\x7f",20,0,0);
    check((const unsigned char *)"abc\x7f\x00",5,0,0);
    check((const unsigned char *)"12345\x7f\x31",7,0,0);
    check((const unsigned char *)"\x7f\x31\x7f\x31",4,0,0);
    recursive=1; check((const unsigned char *)"\x7f\x31",2,0,0); recursive=0;
    unsigned int calls=legacy_calls;
    check((const unsigned char *)"\x7f\x30\x7f\x31",4,0,0);
    assert(legacy_calls==calls+1);
    unsigned char invalid[32]; memset(invalid,'X',sizeof(invalid));
    assert(af_choice_expand(invalid,21,actor)==0 && af_choice_expand(invalid,-1,actor)==0);
    assert(af_choice_expand(0,20,actor)==0);
    for (unsigned int i=0; i<sizeof(invalid); ++i) assert(invalid[i]=='X');
    puts("Complete choice substitutions, padding, atomic bounds, controls, and startup guards pass");
    return 0;
}
