#define main af_previous_font_test
#include "extended_font_test.c"
#undef main

int main(void) {
    static const unsigned char codes[16]={
        0xD0,0xAE,0xA7,0xAB,0xBA,0x2A,0x3B,0x5C,0x60,0x7C,0xBF,0xF7,0x08,0x0A,0x87,0x12
    };
    static const unsigned char advances[16]={3,6,12,12,12,6,12,12,6,6,12,6,6,6,6,6};
    unsigned int i,j,previous;
    unsigned char text[1024];
    assert(!af_previous_font_test());
    word(16,16);memcpy(resource+32,codes,16);memcpy(resource+48,advances,16);
    assert(af_glyph_bind(resource,sizeof(resource)));
    for(i=0;i<256;++i) {
        int expected=-1;
        for(j=0;j<16;++j)if(i==codes[j])expected=(int)j;
        text[0]=0x80;text[1]=(unsigned char)i;
        assert(af_glyph_index(text,2)==expected);
        assert(af_glyph_index(text,1)==-1);
        previous=af_glyph_begin(text,2);
        assert(af_glyph_code_width(0x80,0)==(expected<0?12:advances[expected]));
        assert(af_glyph_texture_code(0x80)==(expected<0?0x80:expected));
        assert(af_glyph_texture()==(expected<0?native_texture:resource+64));
        af_glyph_end(previous);
    }
    for(i=0;i<16;++i) {
        memcpy(damaged,resource,sizeof(resource));damaged[32+i]^=1;
        assert(!af_glyph_bind(damaged,sizeof(resource)));
        memcpy(damaged,resource,sizeof(resource));damaged[48+i]=0;
        assert(!af_glyph_bind(damaged,sizeof(resource)));
    }
    memcpy(text,"Se\x80\x87or K.K.",11);
    assert(af_glyph_string_width(text,11)==60);
    for(i=0;i<1024;i+=2){text[i]=0x80;text[i+1]=0x87;}
    assert(af_glyph_string_width(text,1024)==3072);
    word(16,14);memset(resource+46,0,2);memset(resource+62,0,2);
    assert(af_glyph_bind(resource,sizeof(resource)));
    assert(af_glyph_index((const unsigned char *)"\x80\x87",2)==-1);
    assert(af_glyph_index((const unsigned char *)"\x80\x12",2)==-1);
    assert(af_glyph_index((const unsigned char *)"\x80\x7C",2)==9);
    puts("sixteen-cell accent font primitives passed");
    return 0;
}
