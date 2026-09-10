#include <assert.h>
#include <stdio.h>
#include "core.h"

int main(int argc, char **argv) {
    unsigned char raw[480];
    unsigned short keys[240], output;
    struct { unsigned int before; struct af_grid_state state; unsigned int after; } guard;
    struct af_grid_state *s=&guard.state;
    unsigned int i, expected, skull=0, sun=0;
    FILE *input;
    assert(argc==2);
    input=fopen(argv[1],"rb"); assert(input);
    assert(fread(raw,1,sizeof(raw),input)==sizeof(raw)); assert(fgetc(input)==EOF); fclose(input);
    for (i=0;i<240;++i) keys[i]=(unsigned short)((raw[i*2]<<8)|raw[i*2+1]);
    guard.before=0xBADCAFEu; guard.after=0x12345678u;
    af_grid_reset(s); s->upper=1;
    for (i=0;i<4;++i) {
        assert(af_grid_update(s,keys,0x2000,0x2000,0,0,1,0,&output)==AF_GRID_NONE);
        assert(s->page==((i+1)%2));
        assert(af_grid_update(s,keys,0x2000,0,0,0,1,0,&output)==AF_GRID_NONE);
        assert(s->page==((i+1)%2));
    }
    s->page=1;
    for (i=0;i<40;++i) {
        s->row=(unsigned char)(i/10); s->column=(unsigned char)(i%10);
        expected=keys[160+i];
        if (expected==AF_GRID_SKULL) ++skull;
        if (expected==AF_GRID_SUN) ++sun;
        assert(af_grid_key(s,keys,1,1)==expected);
        assert(af_grid_key(s,keys,1,0)==(expected>255 ? AF_GRID_DISABLED : expected));
        assert(af_grid_key(s,keys,0,0)==(expected>255 || expected==0xCD ? AF_GRID_DISABLED : expected));
        assert(af_grid_update(s,keys,0x8000,0x8000,0,0,1,1,&output)==
               (expected==AF_GRID_DISABLED ? AF_GRID_NONE : AF_GRID_INSERT));
        assert(output==expected);
    }
    assert(skull==1 && sun==1);
    s->page=2;
    assert(af_grid_key(s,keys,1,1)==AF_GRID_DISABLED);
    assert(af_grid_update(s,keys,0x8000,0x8000,0,0,1,1,&output)==AF_GRID_NONE);
    assert(s->page==0 && s->row==0 && s->column==0);
    assert(guard.before==0xBADCAFEu && guard.after==0x12345678u);
    return 0;
}
