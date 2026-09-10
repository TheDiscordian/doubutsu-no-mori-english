#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "core.h"

static unsigned short keys[240];
static unsigned short output;
static int step(struct af_grid_state *s, unsigned int held, unsigned int pressed) {
    return af_grid_update(s,keys,held,pressed,0,0,1,0,&output);
}

int main(int argc, char **argv) {
    struct { unsigned int before; struct af_grid_state grid; unsigned int after; } guarded;
    struct af_grid_state *s=&guarded.grid;
    unsigned char bytes[480];
    unsigned int i;
    FILE *input;
    assert(argc==2);
    input=fopen(argv[1],"rb");assert(input);
    assert(fread(bytes,1,sizeof(bytes),input)==sizeof(bytes));assert(fgetc(input)==EOF);fclose(input);
    for (i=0;i<240;++i) keys[i]=(unsigned short)((bytes[i*2]<<8)|bytes[i*2+1]);
    guarded.before=0xBADCAFEu;guarded.after=0x12345678u;
    af_grid_reset(s);
    assert(sizeof(*s)==12);
    assert(af_grid_key(s,keys,1,0)=='!');
    s->row=1;
    assert(af_grid_key(s,keys,1,0)=='q');
    assert(step(s,0x20,0x20)==AF_GRID_NONE && s->upper==1);
    assert(af_grid_key(s,keys,1,0)=='Q');
    assert(step(s,0x2020,0x2000)==AF_GRID_NONE && s->alphabetical==1);
    assert(af_grid_key(s,keys,1,0)=='A');
    assert(step(s,0x8000,0x8000)==AF_GRID_INSERT && output=='A');
    assert(step(s,0x8000,0)==AF_GRID_NONE); /* A never auto-types while held. */
    assert(step(s,0x10,0x10)==AF_GRID_INSERT && output==' ');
    assert(step(s,0x1000,0x1000)==AF_GRID_DONE);
    assert(step(s,0x2000,0x2000)==AF_GRID_NONE && s->page==1);
    assert(step(s,0x2000,0)==AF_GRID_NONE && s->page==1);
    assert(step(s,0x2000,0x2000)==AF_GRID_NONE && s->page==2);
    s->row=2;s->column=0;
    assert(af_grid_key(s,keys,1,0)==AF_GRID_DISABLED);
    assert(af_grid_key(s,keys,1,1)==AF_GRID_SUN);
    s->row=1;s->column=4;
    assert(af_grid_key(s,keys,1,1)==AF_GRID_SKULL);
    assert(step(s,0x8000,0x8000)==AF_GRID_NONE);
    assert(af_grid_update(s,keys,0x8000,0x8000,0,0,0,1,&output)==AF_GRID_INSERT);
    assert(output==AF_GRID_SKULL);
    s->page=0;s->row=2;s->column=9;s->upper=0;s->alphabetical=0;
    assert(af_grid_key(s,keys,1,0)==0xCD);
    assert(af_grid_key(s,keys,0,0)==AF_GRID_DISABLED);
    s->row=0;s->column=9;
    assert(af_grid_key(s,keys,1,0)==AF_GRID_DISABLED); /* GC's unused key. */
    af_grid_reset(s);
    step(s,0x0100,0x0100);assert(s->column==1);
    for (i=0;i<7;++i) {step(s,0x0100,0);assert(s->column==1);}
    step(s,0x0100,0);assert(s->column==2);
    step(s,0x0100,0);assert(s->column==2);
    step(s,0x0100,0);assert(s->column==3);
    for(i=0;i<100;++i) step(s,0x0100,0);
    assert(s->column==9 && !s->moved);
    step(s,0,0);step(s,0x0200,0x0200);assert(s->column==8);
    step(s,0x0300,0x0300);assert(s->column==8); /* Opposing directions cancel. */
    step(s,0,0);
    af_grid_update(s,keys,0,0,60,0,1,0,&output);assert(s->column==9);
    step(s,0,0);
    af_grid_update(s,keys,0,0,0,-60,1,0,&output);assert(s->row==1);
    step(s,0,0);
    assert(step(s,0x4000,0x4000)==AF_GRID_BACKSPACE);
    for(i=0;i<7;++i) assert(step(s,0x4000,0)==AF_GRID_NONE);
    assert(step(s,0x4000,0)==AF_GRID_BACKSPACE);
    step(s,0,0);
    assert(step(s,1,1)==AF_GRID_RIGHT);
    step(s,0,0);assert(step(s,2,2)==AF_GRID_LEFT);
    step(s,0,0);assert(step(s,4,4)==AF_GRID_DOWN);
    step(s,0,0);assert(step(s,8,8)==AF_GRID_UP);
    s->column=255;assert(step(s,0x8000,0x8000)==AF_GRID_NONE);assert(s->column==0);
    assert(guarded.before==0xBADCAFEu && guarded.after==0x12345678u);
    return 0;
}
