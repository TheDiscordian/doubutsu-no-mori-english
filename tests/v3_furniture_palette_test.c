#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_SHARED_PALETTE_FADE 1
#include "../overlays/v3/tent_model.c"

/* The legacy object stays unchanged; only its immutable layout is separate. */
const PaletteLayout af_v3_legacy_tent_layout = {
    0x41465031,4288,4,32,64,{0x06000C50,0x06000D18,0x06000E00,0x06000FF0}
};
static _Alignas(32) u8 arena[16384], bank[9216];
static TentGfx graphics;
static unsigned matrices, flushes;
void *_Matrix_to_Mtx(void *destination) {
    assert(destination==graphics.tail && !((uptr)destination&31));
    memset(destination,0x7B,64);++matrices;return destination;
}
void osWritebackDCache(void *address,int bytes) {
    assert(address==graphics.tail && bytes==96);++flushes;
}
static u32 big(const u8 *p,int bytes) {
    u32 value=0;while(bytes--)value=value*256+*p++;return value;
}
static void endian_palette(u32 at) {
    for(u32 i=0;i<32;i+=2) { u16 v=big(bank+at+i,2);memcpy(bank+at+i,&v,2); }
}
static void check_palette(const u16 *palette,const PaletteLayout *layout,float fade) {
    const u16 *on=(const u16 *)(bank+layout->on),*off=(const u16 *)(bank+layout->off);
    for(int i=0;i<16;++i) {
        int r=(off[i]>>11)+fade*((int)(on[i]>>11)-(off[i]>>11));
        int g=(off[i]>>6&31)+fade*((int)(on[i]>>6&31)-(off[i]>>6&31));
        int b=(off[i]>>1&31)+fade*((int)(on[i]>>1&31)-(off[i]>>1&31));
        assert(palette[i]==(r<<11|g<<6|b<<1|(off[i]&1)));
    }
}
static const u16 *render(Tent *actor,const PaletteLayout *layout,int legacy) {
    TentGame game={&graphics};Command *head=graphics.head;u8 *tail=graphics.tail;
    unsigned before=matrices;
    if(legacy)af_v3_tent_model_dw(actor,0,&game,bank);
    else af_v3_palette_fade_dw(actor,0,&game,bank);
    assert(matrices==before+1 && matrices==flushes);
    assert(graphics.head==head+layout->count+2 && tail-graphics.tail>=96 && tail-graphics.tail<=112);
    assert(head[0].a==0xDA380003 && head[0].b==(u32)(uptr)graphics.tail);
    assert(head[1].a==0xDB060020 && head[1].b==(u32)(uptr)(graphics.tail+64));
    for(u32 i=0;i<layout->count;++i)assert(head[i+2].a==0xDE000000 && head[i+2].b==layout->models[i]);
    const u16 *result=(const u16 *)(graphics.tail+64);check_palette(result,layout,actor->fade.f);return result;
}
int main(int argc,char **argv) {
    assert(argc>=3);
    for(int file_index=1;file_index<argc;++file_index) {
        int legacy=file_index==1;
        FILE *file=fopen(argv[file_index],"rb");assert(file);
        size_t bytes=fread(bank,1,sizeof bank,file);assert(bytes && fgetc(file)==EOF && !fclose(file));
        PaletteLayout layout=af_v3_legacy_tent_layout;
        if(!legacy) {
            layout.magic=big(bank,4);layout.bytes=big(bank+4,2);layout.count=big(bank+6,2);
            layout.on=big(bank+8,4);layout.off=big(bank+12,4);
            for(int i=0;i<4;++i)layout.models[i]=big(bank+16+4*i,4);
            memcpy(bank,&layout,sizeof layout);
        }
        assert(layout.bytes==bytes);endian_palette(layout.on);endian_palette(layout.off);
        Tent actors[2],original;memset(actors,0xA5,sizeof actors);memset(arena,0xA5,sizeof arena);
        graphics.head=(Command *)(arena+32);graphics.tail=arena+sizeof arena-32;
        for(int i=0;i<2;++i) {
            actors[i].switch_bit=i;original=actors[i];af_v3_tent_model_ct(actors+i,bank);
            assert(actors[i].fade.f==i);original.fade=actors[i].fade;assert(!memcmp(&original,actors+i,sizeof original));
        }
        const u16 *first=render(actors,&layout,legacy),*second=render(actors+1,&layout,legacy);
        float expected[2]={0,1};
        for(int frame=0;frame<24;++frame)for(int i=0;i<2;++i) {
            actors[i].switch_bit=frame<4||frame>=8?!i:i;float target=actors[i].switch_bit;
            if(expected[i]>target) { expected[i]-=0.1f;if(expected[i]<target)expected[i]=target; }
            else if(expected[i]<target) { expected[i]+=0.1f;if(expected[i]>target)expected[i]=target; }
            original=actors[i];af_v3_tent_model_mv(actors+i,0,0,bank);assert(actors[i].fade.f==expected[i]);
            original.fade=actors[i].fade;assert(!memcmp(&original,actors+i,sizeof original));
            render(actors+i,&layout,legacy);check_palette(first,&layout,0);check_palette(second,&layout,1);
        }
        for(int i=0;i<2;++i) { af_v3_tent_model_dt(actors+i,bank);assert(actors[i].fade.bits==0); }
        check_palette(first,&layout,0);check_palette(second,&layout,1);
        TentGame game={&graphics};
        for(int available=0;available<=176;available+=8) {
            graphics.head=(Command *)(arena+32);graphics.tail=arena+32+available;
            Command *head=graphics.head;u8 *tail=graphics.tail;unsigned before=matrices;
            uptr allocation=available>=96?((uptr)tail-96)&~(uptr)31:0;
            int fits=!((uptr)tail&15) && available>=(int)(96+(layout.count+2)*8) &&
                     allocation>=(uptr)head+(layout.count+2)*8;
            if(legacy)af_v3_tent_model_dw(actors,0,&game,bank);else af_v3_palette_fade_dw(actors,0,&game,bank);
            if(fits)assert(matrices==before+1);
            else assert(matrices==before && graphics.head==head && graphics.tail==tail);
        }
        if(!legacy)for(int field=0;field<7;++field) {
            PaletteLayout bad=layout;
            switch(field) {
            case 0:bad.magic=0;break;case 1:bad.bytes=32;break;case 2:bad.count=5;break;
            case 3:bad.on=layout.bytes;break;case 4:bad.off=33;break;
            case 5:bad.models[0]=0x08000000;break;case 6:bad.models[2]=0x06000001;break;
            }
            memcpy(bank,&bad,sizeof bad);unsigned before=matrices;
            graphics.head=(Command *)(arena+32);graphics.tail=arena+sizeof arena-32;
            af_v3_palette_fade_dw(actors,0,&game,bank);assert(matrices==before);
        }
        for(int i=0;i<32;++i)assert(arena[i]==0xA5 && arena[sizeof arena-1-i]==0xA5);
    }
    puts("Shared palette layouts, full source colours, independent fades, retained frames, bounds, and actor guards pass");
}
