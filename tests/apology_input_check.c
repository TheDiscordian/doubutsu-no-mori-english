#include <assert.h>
#include <string.h>
#include "edit.h"

struct guarded { unsigned char before[16]; struct af_apology_draft draft; unsigned char after[16]; };

static void fresh(struct guarded *g) {
    memset(g,0xA5,sizeof(*g));
    memset(g->draft.text,' ',AF_APOLOGY_BYTES);
    g->draft.length=g->draft.cursor=0;
}
static void guards(const struct guarded *g) {
    unsigned int i;
    for (i=0;i<16;++i) assert(g->before[i]==0xA5 && g->after[i]==0xA5);
}
static void put(struct guarded *g, int code) {
    assert(af_apology_edit(&g->draft,AF_APOLOGY_INSERT,code)==AF_APOLOGY_CHANGED);
    assert(af_apology_valid(&g->draft)); guards(g);
}
static void unchanged(struct guarded *g, int command, int code, int result) {
    struct guarded original=*g;
    assert(af_apology_edit(&g->draft,command,code)==result);
    assert(!memcmp(g,&original,sizeof(*g))); guards(g);
}
static void sentence(struct guarded *g,const char *prefix,int code,const char *suffix,const unsigned char *expected) {
    fresh(g);
    while (*prefix) put(g,(unsigned char)*prefix++);
    put(g,code);
    while (*suffix) put(g,(unsigned char)*suffix++);
    assert(g->draft.length==10 && g->draft.cursor==10);
    assert(!memcmp(g->draft.text,expected,10));
    unchanged(g,AF_APOLOGY_INSERT,'!',AF_APOLOGY_FULL);
    unchanged(g,AF_APOLOGY_RIGHT,0,AF_APOLOGY_FULL);
    unchanged(g,AF_APOLOGY_DONE,0,AF_APOLOGY_FINISHED);
}

int main(void) {
    struct guarded g;
    unsigned int code,at;
    const unsigned char sun[10]={'U',' ','R',' ','m','y',' ',0x80,0xA7,'!'};
    const unsigned char skull[10]={'R','e','s','e','t',' ','=',' ',0x80,0xBA};
    sentence(&g,"U R my ",AF_APOLOGY_SUN,"!",sun);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_LEFT,0)==1 && g.draft.cursor==9);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_LEFT,0)==1 && g.draft.cursor==7);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_RIGHT,0)==1 && g.draft.cursor==9);
    unchanged(&g,AF_APOLOGY_EXCHANGE,'x',AF_APOLOGY_UNCHANGED);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_BACKSPACE,0)==1);
    assert(g.draft.length==8 && g.draft.cursor==7 && !memcmp(g.draft.text,"U R my !  ",10));
    put(&g,AF_APOLOGY_SUN);assert(!memcmp(g.draft.text,sun,10));
    sentence(&g,"Reset = ",AF_APOLOGY_SKULL,"",skull);
    unchanged(&g,AF_APOLOGY_EXCHANGE,'x',AF_APOLOGY_UNCHANGED);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_BACKSPACE,0)==1 && g.draft.length==8);
    put(&g,AF_APOLOGY_SKULL);assert(!memcmp(g.draft.text,skull,10));

    /* Every insertion point and both pair widths preserve neighbours/tail. */
    for (at=0;at<=8;++at) {
        fresh(&g);for (code=0;code<8;++code)put(&g,'a'+(int)code);
        g.draft.cursor=(unsigned char)at;put(&g,AF_APOLOGY_SUN);
        assert(g.draft.cursor==at+2 && g.draft.length==10);
        assert(af_apology_edit(&g.draft,AF_APOLOGY_BACKSPACE,0)==1);
        assert(g.draft.cursor==at && g.draft.length==8 && !memcmp(g.draft.text,"abcdefgh  ",10));
        guards(&g);
    }
    fresh(&g);for(at=0;at<5;++at)put(&g,at&1?AF_APOLOGY_SUN:AF_APOLOGY_SKULL);
    for(at=10;at>0;at-=2){assert(g.draft.cursor==at);assert(af_apology_edit(&g.draft,AF_APOLOGY_LEFT,0)==1);}
    for(at=0;at<10;at+=2){assert(g.draft.cursor==at);assert(af_apology_edit(&g.draft,AF_APOLOGY_RIGHT,0)==1);}
    for(at=0;at<5;++at)assert(af_apology_edit(&g.draft,AF_APOLOGY_BACKSPACE,0)==1);
    assert(!memcmp(g.draft.text,"          ",10));
    unchanged(&g,AF_APOLOGY_BACKSPACE,0,0);unchanged(&g,AF_APOLOGY_LEFT,0,0);
    unchanged(&g,AF_APOLOGY_UP,0,0);unchanged(&g,AF_APOLOGY_DOWN,0,0);
    unchanged(&g,AF_APOLOGY_INSERT,0xCD,0);
    assert(af_apology_edit(&g.draft,AF_APOLOGY_RIGHT,0)==1 && g.draft.length==1);
    put(&g,'a');assert(af_apology_edit(&g.draft,AF_APOLOGY_EXCHANGE,'A')==1 && g.draft.text[1]=='A');
    unchanged(&g,AF_APOLOGY_EXCHANGE,AF_APOLOGY_SKULL,AF_APOLOGY_ARGUMENT);
    unchanged(&g,AF_APOLOGY_EXCHANGE,-1,0);

    for(code=0;code<256;++code) {
        fresh(&g);
        if(code==0x7F || code==0x80) unchanged(&g,AF_APOLOGY_INSERT,(int)code,AF_APOLOGY_ARGUMENT);
        else if(code==0xCD)unchanged(&g,AF_APOLOGY_INSERT,(int)code,0);
        else put(&g,(int)code);
        fresh(&g);
        if(code==0xA7 || code==0xBA)put(&g,0x8000|(int)code);
        else unchanged(&g,AF_APOLOGY_INSERT,0x8000|(int)code,AF_APOLOGY_ARGUMENT);
    }
    fresh(&g);put(&g,AF_APOLOGY_SUN);g.draft.cursor=1;
    unchanged(&g,AF_APOLOGY_BACKSPACE,0,AF_APOLOGY_ARGUMENT);
    g.draft.cursor=0;g.draft.length=1;
    unchanged(&g,AF_APOLOGY_INSERT,'x',AF_APOLOGY_ARGUMENT);
    fresh(&g);g.draft.text[9]='x';unchanged(&g,AF_APOLOGY_DONE,0,AF_APOLOGY_ARGUMENT);
    fresh(&g);g.draft.cursor=11;unchanged(&g,AF_APOLOGY_DONE,0,AF_APOLOGY_ARGUMENT);
    fresh(&g);g.draft.length=11;unchanged(&g,AF_APOLOGY_DONE,0,AF_APOLOGY_ARGUMENT);
    fresh(&g);unchanged(&g,0,0,AF_APOLOGY_ARGUMENT);unchanged(&g,9,0,AF_APOLOGY_ARGUMENT);
    unchanged(&g,AF_APOLOGY_INSERT,-1,AF_APOLOGY_ARGUMENT);
    unchanged(&g,AF_APOLOGY_INSERT,0x10000,AF_APOLOGY_ARGUMENT);
    assert(!af_apology_valid(0));assert(af_apology_edit(0,8,'a')==AF_APOLOGY_ARGUMENT);
    return 0;
}
