#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "font.h"

static unsigned char resource[AF_GLYPH_BYTES] __attribute__((aligned(16)));
static unsigned char damaged[AF_GLYPH_BYTES+16] __attribute__((aligned(16)));
static unsigned char native_texture[16];
const unsigned char *af_glyph_native_texture(void) { return native_texture; }
unsigned int af_glyph_native_offset(unsigned int code) {
    if (code=='i' || code=='I' || code=='l' || code=='\'') return 8;
    return code>=32 && code<127 ? 6 : 0;
}
static void word(unsigned int offset,unsigned int value) {
    resource[offset]=(unsigned char)(value>>24);
    resource[offset+1]=(unsigned char)(value>>16);
    resource[offset+2]=(unsigned char)(value>>8);
    resource[offset+3]=(unsigned char)value;
}
int main(void) {
    static const unsigned char codes[5]={0xD0,0xAE,0xA7,0xAB,0xBA};
    static const unsigned char advances[5]={3,6,12,12,12};
    unsigned char text[1025];unsigned int i,j,previous;
    assert(!af_glyph_bind(NULL,1600));
    af_glyph_end(1); assert(af_glyph_texture()==native_texture);
    assert(af_glyph_index((const unsigned char *)"\x80\xD0",2)==-1);
    word(0,0x41464758);word(4,1);word(8,192);word(12,16);word(16,5);word(20,64);word(24,1536);
    memcpy(resource+32,codes,5);memcpy(resource+48,advances,5);
    assert(af_glyph_bind(resource,sizeof(resource)));
    for (i=0;i<256;++i) {
        text[0]=0x80;text[1]=(unsigned char)i;
        int expected=-1;
        for (j=0;j<5;++j) if (i==codes[j]) expected=(int)j;
        assert(af_glyph_index(text,2)==expected);
        assert(af_glyph_index(text,1)==-1);
        assert(af_glyph_index(text,0)==-1);
        assert(af_glyph_index(NULL,2)==-1);
        assert(af_glyph_size(text,2)==(expected<0?1u:2u));
        previous=af_glyph_begin(text,2); assert(previous==0);
        assert(af_glyph_code_width(0x80,0)==(expected<0?12:advances[expected]));
        assert(af_glyph_code_width(0x80,1)==(expected<0?12:advances[expected]));
        assert(af_glyph_texture_code(0x80)==(expected<0?0x80:expected));
        assert(af_glyph_texture()==(expected<0?native_texture:resource+64));
        assert(af_glyph_code_width('i',1)==4);
        assert(af_glyph_code_width(0xE0,0)==12);
        assert(af_glyph_texture_code('A')=='A');
        if (expected>=0) {
            assert(!af_glyph_bind(resource,sizeof(resource)));
            unsigned int nested=af_glyph_begin((const unsigned char *)"A",1);
            assert(nested==(unsigned int)expected+1 && af_glyph_texture()==native_texture);
            af_glyph_end(nested); assert(af_glyph_texture()==resource+64);
        }
        af_glyph_end(previous);assert(af_glyph_texture()==native_texture);
    }
    for (i=0;i<32;++i) {
        memcpy(damaged,resource,sizeof(resource));damaged[i]^=1;
        assert(!af_glyph_bind(damaged,sizeof(resource)));
    }
    memcpy(damaged+1,resource,sizeof(resource));assert(!af_glyph_bind(damaged+1,sizeof(resource)));
    assert(!af_glyph_bind(resource,1599));assert(!af_glyph_bind(resource,1601));
    memcpy(text,"i\x80\xD0I\x80\xAE\x80\xA7",8);
    assert(af_glyph_string_width(text,8)==30);
    assert(af_glyph_string_width(text,0)==0);
    assert(af_glyph_string_width(NULL,1)==-1);
    assert(af_glyph_string_width(text,1025)==-1);
    /* Every possible final byte is bounded; unknown tags keep native byte widths. */
    for (i=0;i<256;++i) {
        text[0]=(unsigned char)i;
        assert(af_glyph_string_width(text,1)==(int)((13-af_glyph_native_offset(i))&~1u));
    }
    memset(text,'i',1024);assert(af_glyph_string_width(text,1024)==4096);
    assert(af_glyph_code_width(256,1)==12);
    assert(af_glyph_code_width(~0u,1)==12);
    puts("extended font primitives passed");
    return 0;
}
