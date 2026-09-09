#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "../overlays/world_names/names.h"
#include "../overlays/extended_font/font.h"

static struct { unsigned char before[16]; float fields[10]; unsigned char after[16]; } memory;
static unsigned char glyphs[1600] __attribute__((aligned(16)));
static unsigned char supplied[16], drawn[16];
static int loads, legacy_loads, reject, draws;
static float expected_x;
float *state(void) { return memory.fields; }
const unsigned char *af_glyph_native_texture(void) { return glyphs; }
unsigned int af_glyph_native_offset(unsigned int c) { return c=='i' || c=='I' || c=='\'' ? 9 : 6; }
void native_zero(void *destination, int bytes) { assert(bytes==40); memset(destination,0,40); }
void native_name(unsigned char *destination, unsigned short item) {
    assert(item==0x2001); ++legacy_loads; memcpy(destination,"native ten",10);
}
int full_name(unsigned char *destination, unsigned int capacity, unsigned int item) {
    assert(capacity==16 && item==0x2001); ++loads;
    memset(destination,'?',16); /* Even a partially writing failure cannot leak. */
    if (reject) return 0;
    memcpy(destination,supplied,16); return 1;
}
float native_draw(void *game, const unsigned char *text, int length, float x, float y,
                  int r,int g,int b,int a,int reverse,int cut,float sx,float sy,int mode) {
    assert(game==&memory && length==16 && x==expected_x && y==113.0f);
    assert(r==45 && g==45 && b==35 && a==173 && !reverse && !cut);
    assert(sx==0.875f && sy==0.875f && mode==1);
    memcpy(drawn,text,16); ++draws; return 12.5f;
}
static void render(const unsigned char *expected) {
    unsigned char old[40]; int n=16, pixels, previous_loads=loads;
    while(n && expected[n-1]==' ') --n;
    pixels=af_glyph_string_width(expected,(unsigned int)n);
    memcpy(old,memory.fields,40);
    af_world_measure();
    assert(memory.fields[5] == (pixels<24 ? 0.0f : ((float)pixels/12.0f-2.0f)/8.0f));
    memcpy(old+20,(unsigned char *)memory.fields+20,4);
    assert(!memcmp(old,memory.fields,40));
    expected_x=memory.fields[0]+160.0f-(float)pixels*0.875f*0.5f;
    assert(af_world_draw(&memory,(unsigned char *)memory.fields+29,10,-999.0f,113.0f,
                         45,45,35,173,0,0,0.875f,0.875f,1)==12.5f);
    assert(!memcmp(drawn,expected,16) && loads==previous_loads);
}
static void guards(void) {
    unsigned int i;
    for(i=0;i<16;++i) assert(memory.before[i]==0xA5 && memory.after[i]==0xA5);
}

/* Startup hook tests use a private code map, never live native addresses. */
static unsigned int code[(0x800CC9C4u-0x800CBF80u)/4], old_code[sizeof(code)/sizeof(code[0])];
static int font_ok, font_calls, flushes;
static const unsigned int addresses[]={0x800CBF90,0x800CC324,0x800CC32C,0x800CC330,
    0x800CC334,0x800CC338,0x800CC33C,0x800CC340,0x800CC9A8};
static const unsigned int originals[]={0x0C00BD30,0x0C0259D0,0x3C048014,0x248446BD,
    0x2405000A,0x0C027070,0x24060020,0x44829000,0x0C0243A6};
volatile unsigned int *af_world_test_word(unsigned int address) {
    assert(address>=0x800CBF80u && address<0x800CC9C4u && !(address&3));
    return code+(address-0x800CBF80u)/4;
}
void af_world_test_flush(void) { ++flushes; }
int af_font_install(void) { ++font_calls; return font_ok; }
extern int af_world_font_install(void);
static void setup(void) {
    unsigned int i;
    for(i=0;i<sizeof(code)/sizeof(code[0]);++i) code[i]=0xDEADBEEFu;
    for(i=0;i<9;++i) *af_world_test_word(addresses[i])=originals[i];
    font_ok=1; font_calls=flushes=0;
}
static unsigned int call(const void *fn) { return 0x0C000000u|(((unsigned int)(uintptr_t)fn&0x0FFFFFFFu)>>2); }
static void installation(void) {
    unsigned int i, j, patched[]={call(af_world_reset),call(af_world_load),call(af_world_measure),
        0,0x3C088014,0x250846A0,0x080330DB,0,call(af_world_draw)};
    for(i=0;i<9;++i) {
        setup(); *af_world_test_word(addresses[i])^=1; memcpy(old_code,code,sizeof(code));
        assert(!af_world_font_install() && !font_calls && !flushes);
        assert(!memcmp(old_code,code,sizeof(code)));
    }
    setup();font_ok=0;memcpy(old_code,code,sizeof(code));
    assert(!af_world_font_install() && font_calls==1 && !flushes);
    assert(!memcmp(old_code,code,sizeof(code)));
    setup();assert(af_world_font_install() && font_calls==1 && flushes==1);
    for(i=0;i<sizeof(code)/sizeof(code[0]);++i) {
        unsigned int expected=0xDEADBEEFu;
        for(j=0;j<9;++j) if(0x800CBF80u+i*4==addresses[j]) expected=patched[j];
        assert(code[i]==expected);
    }
    memcpy(old_code,code,sizeof(code));
    assert(!af_world_font_install() && font_calls==1 && flushes==1);
    assert(!memcmp(old_code,code,sizeof(code)));
}

int main(int argc,char **argv) {
    FILE *file; unsigned char *native=(unsigned char *)memory.fields;
    assert(argc==2);file=fopen(argv[1],"rb");assert(file);
    assert(fread(glyphs,1,1600,file)==1600);fclose(file);
    assert(af_glyph_bind(glyphs,1600));
    memset(&memory,0xA5,sizeof(memory)); af_world_reset(memory.fields,40);
    render((const unsigned char *)"                ");guards();
    memory.fields[0]=17.0f; native[28]=3;native[39]=1;
    memcpy(supplied,"abcdefghijklmnop",16);
    af_world_load(native+29,0x2001);render(supplied);
    assert(!memcmp(native+29,"native ten",10) && native[28]==3 && native[39]==1);guards();
    memcpy(supplied,"iI'             ",16);
    af_world_load(native+29,0x2001);render(supplied);
    assert(memory.fields[5]==0.0f); /* Narrow names must not invert the mesh. */
    memcpy(supplied,"caf\x80\x08            ",16);
    af_world_load(native+29,0x2001);render(supplied);
    reject=1;af_world_load(native+29,0x2001);render((const unsigned char *)"Name unavailable");
    reject=0;af_world_load(native+29,0x2001);render(supplied);
    af_world_reset(memory.fields,40);render((const unsigned char *)"                ");guards();
    assert(loads==5 && legacy_loads==5 && draws==7);
    installation(); puts("world storage, geometry, and atomic installation passed");return 0;
}
