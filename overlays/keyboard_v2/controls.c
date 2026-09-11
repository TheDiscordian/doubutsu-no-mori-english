/* Native N64 artwork, read from the already loaded keyboard resource.
 * No input state, editor storage, or texture pixels are modified here. */
struct af_v2_icon {
    unsigned int texture, pressed, mask;
    unsigned short button;
    unsigned char width, height;
    unsigned short x, y;
    unsigned char w, h, mirror, yellow;
};

static const struct af_v2_icon af_v2_icons[] = {
    /* Animated stick. The transparent margins keep its ink left of the keys. */
    {0xD648,0xD648,0,0,64,64,18,137,48,48,0,0},
    /* The native shoulder image has no letter; mirror it for the L shoulder. */
    {0x8E48,0x8648,0,0x20,64,32,112,118,18,9,1,0},
    {0xCE48,0xC648,0,0x2000,32,64,161,112,9,18,0,0},
    {0x14648,0x16448,0x14E48,0x8000,32,32,70,199,14,14,0,0},
    {0x13E48,0x15C48,0x14E48,0x4000,32,32,113,199,14,14,0,0},
    {0x8E48,0x8648,0,0x10,64,32,157,202,18,9,0,0},
    {0x13648,0x15448,0x14E48,0x1000,32,32,213,199,14,14,0,0},
    /* Four separate C buttons, not a GameCube C stick. */
    {0x6348,0x6248,0,0x8,16,16,248,147,10,10,0,1},
    {0x6148,0x6048,0,0x2,16,16,238,157,10,10,0,1},
    {0x5F48,0x5E48,0,0x1,16,16,258,157,10,10,0,1},
    {0x6548,0x6448,0,0x4,16,16,248,167,10,10,0,1},
};

static Gfx *af_v2_controls(Gfx *g, float dx, float dy) {
    unsigned int i, held=af_grid_get_button();
    unsigned int stick=af_v2_stick(held,af_grid_get_x(),af_grid_get_y());
    for (i=0;i<sizeof(af_v2_icons)/sizeof(af_v2_icons[0]);++i) {
        const struct af_v2_icon *p=&af_v2_icons[i];
        unsigned int down=held&p->button;
        unsigned int frame=down ? p->pressed : p->texture, mirror=p->mirror;
        const void *texture;
        if (!i) {frame=0xD648u+(stick&15u)*0x1000u;mirror=stick>>4;}
        texture=(const void *)(0x0C000000u+frame);
        int x=(int)(p->x+dx), y=(int)(p->y-dy);
        int ds=(p->width*1024+p->w/2)/p->w, dt=(p->height*1024+p->h/2)/p->h;
        if (x<0 || y<0 || x+p->w>320 || y+p->h>240) continue;
        gDPPipeSync(g++);
        if (p->mask) {
            /* Original two-texture material: RGBA colour with soft I4 alpha.
               Drawing the RGB tile alone would leave a coloured square. */
            gDPSetCycleType(g++,G_CYC_2CYCLE);
            gDPSetRenderMode(g++,G_RM_PASS,G_RM_XLU_SURF2);
            gDPSetCombineLERP(g++,0,0,0,TEXEL0,0,0,0,TEXEL1,
                                 0,0,0,COMBINED,0,0,0,COMBINED);
            gDPLoadTextureBlock(g++,texture,G_IM_FMT_RGBA,G_IM_SIZ_16b,32,32,0,
                               G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
            gDPLoadMultiBlock_4b(g++,(const void *)(0x0C000000u+(down ? 0x16C48 : p->mask)),
                                256,1,G_IM_FMT_I,32,32,0,G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
        } else {
            gDPSetCycleType(g++,G_CYC_1CYCLE);
            gDPSetRenderMode(g++,G_RM_XLU_SURF,G_RM_XLU_SURF2);
            gDPSetCombineMode(g++,G_CC_BLENDPEDECALA,G_CC_BLENDPEDECALA);
            gDPSetPrimColor(g++,0,255,p->yellow ? 255 : 225,p->yellow ? 215 : 225,
                           p->yellow ? 35 : 225,255);
            gDPSetEnvColor(g++,p->yellow ? 100 : 50,p->yellow ? 65 : 50,
                          p->yellow ? 0 : 50,255);
            gDPLoadTextureBlock(g++,texture,G_IM_FMT_IA,G_IM_SIZ_8b,p->width,p->height,0,
                               G_TX_CLAMP,G_TX_CLAMP,0,0,0,0);
        }
        gSPTextureRectangle(g++,x*4,y*4,(x+p->w)*4,(y+p->h)*4,0,
                            mirror ? (p->width-1)*32 : 0,0,mirror ? -ds : ds,dt);
    }
    gDPPipeSync(g++);
    gDPSetCycleType(g++,G_CYC_1CYCLE);
    gDPSetRenderMode(g++,G_RM_XLU_SURF,G_RM_XLU_SURF2);
    return g;
}

static void af_v2_labels(void *graph, void *game, float dx, float dy) {
    unsigned int held=af_grid_get_button();
    label(graph,game,"Case",132+dx,117-dy);
    label(graph,game,"Page",173+dx,117-dy);
    /* The left margin has room for the stick, not another full-size label.
       Movement is labelled in the bottom control hint. */
    label(graph,game,"Cursor",242+dx,180-dy);
    label(graph,game,"Type",86+dx,200-dy);
    label(graph,game,"Del",129+dx,200-dy);
    label(graph,game,"Space",177+dx,200-dy);
    label(graph,game,"Done",230+dx,200-dy);
    text(graph,game,(const unsigned char *)"L",1,117.5f+dx,115-dy+!!(held&0x20),0,0,0.6f);
    text(graph,game,(const unsigned char *)"R",1,162.5f+dx,199-dy+!!(held&0x10),0,0,0.6f);
    text(graph,game,(const unsigned char *)"A",1,74.5f+dx,199-dy+!!(held&0x8000),1,0,0.65f);
    text(graph,game,(const unsigned char *)"B",1,118+dx,199-dy+!!(held&0x4000),1,0,0.65f);
    centred_label(graph,game,"D-pad: Move   L+A: Alter   L+Z: ABC",160+dx,212-dy);
}
