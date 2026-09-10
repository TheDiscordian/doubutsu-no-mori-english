/* Isolated renderer comparison; never linked into a translation cartridge. */
#include <PR/mbi.h>

#define WORD(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define META ((volatile u32 *)0x80503000)
typedef struct { float x,y; } Point;
typedef void (*Mode)(Gfx **);
typedef void (*Matrix)(void *,int);
typedef void (*Rect)(void *,Gfx **,int,u32,u32,u32,u32,int,int);
typedef void (*Poly)(void *,Gfx **,int,Point *,Point *,int,int);
typedef int (*Width)(unsigned int,int);

void af_font_preview(void *actor,void *game) {
    static const unsigned char text[]="AB gijpqy 01";
    static const Vp viewport={{{640,480,511,0},{640,480,511,0}}};
    void *graph=*(void **)game;
    Gfx *p=(Gfx *)WORD(graph,0x288), *end=(Gfx *)WORD(graph,0x28C);
    u32 saved_font=WORD(graph,0x2B8),row,i,k;
    (void)actor;
    if ((u32)p+6200>(u32)end || WORD(graph,0x29C)<WORD(graph,0x298)+4096) {
        META[2]=1; return;
    }
    gDPPipeSync(p++);
    gDPSetScissor(p++,G_SC_NON_INTERLACE,0,0,320,240);
    gDPSetCycleType(p++,G_CYC_FILL);
    gDPSetRenderMode(p++,G_RM_NOOP,G_RM_NOOP2);
    gDPSetColorImage(p++,G_IM_FMT_RGBA,G_IM_SIZ_16b,320,WORD(graph,0x2E4));
    gDPSetFillColor(p++,0xFFFFFFFF);
    gDPFillRectangle(p++,0,0,319,239);
    gDPPipeSync(p++);
    gSPViewport(p++,&viewport);
    WORD(graph,0x2B8)=(u32)p;
    ((Matrix)0x80090F10)(graph,1);
    p=(Gfx *)WORD(graph,0x2B8);
    WORD(graph,0x2B8)=saved_font;
    for (row=0;row<4;++row) {
        float x=32.0f,y=24.0f+row*48.0f;
        float scale=META[0] ? 1.0f : 2.0f;
        ((Mode)0x800903E4)(&p);
        gDPPipeSync(p++);
        gDPSetPrimColor(p++,0,0,24,24,24,255);
        gDPSetTexturePersp(p++,row ? G_TP_PERSP : G_TP_NONE);
        for (i=0;i<sizeof(text)-1;++i) {
            int width=((Width)0x8009028C)(text[i],1);
            if (row==0) {
                ((Rect)0x8009113C)(graph,&p,text[i],(u32)(x*4),(u32)(y*4),
                    (u32)((x+width*scale)*4),(u32)((y+16*scale)*4),
                    (int)(1024/scale),(int)(1024/scale));
            } else {
                Point tl={x,y},br={x+width*scale,y+16*scale};
                Gfx *start=p;
                Vtx *v;
                int offset=row==3 ? 32 : 0;
                if (row>=2) {tl.x-=scale;tl.y-=scale;br.x+=scale;br.y+=scale;}
                ((Poly)0x800911E8)(graph,&p,text[i],&tl,&br,width+(row>=2 ? 2 : 0),row>=2 ? 18 : 16);
                v=(Vtx *)WORD(graph,0x29C);
                if (row>=2) {
                    Gfx *load=start;
                    gDPLoadTextureBlock_4b(load++,(void *)(0x80504000+i*144),G_IM_FMT_I,16,18,0,
                        G_TX_CLAMP,G_TX_CLAMP,0,0,0,0);
                    if (load!=start+7) {META[2]=2;return;}
                    for (k=0;k<4;++k) {
                        v[k].v.tc[0]=(k>=2 ? (width+2)*64 : 0)+offset;
                        v[k].v.tc[1]=(k==1 || k==2 ? 18*64 : 0)+offset;
                    }
                }
            }
            x+=width*scale;
        }
    }
    ((Matrix)0x8009104C)(graph,1);
    WORD(graph,0x288)=(u32)p;
    META[1]++;
    META[3]=(u32)p;
    META[4]=(u32)end;
    META[5]=WORD(graph,0x2E4);
}
