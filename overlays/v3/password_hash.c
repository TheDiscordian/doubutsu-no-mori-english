/* Private # glyph from the supplied disc, without changing the shared font. */
static void af_pw_hash_draw(void *graph, float fx, float fy, int r, int gcol, int b) {
    Gfx *g;
    int x=(int)fx, y=(int)fy;
    if (x<0 || y<0 || x+16>320 || y+16>240 || !space(graph,512)) return;
    g=PTR(graph,0x298);
    gDPPipeSync(g++); gDPSetCycleType(g++,G_CYC_1CYCLE);
    gDPSetRenderMode(g++,G_RM_XLU_SURF,G_RM_XLU_SURF2);
    gDPSetTextureLUT(g++,G_TT_NONE); gDPSetTexturePersp(g++,G_TP_NONE);
    gDPSetDepthSource(g++,G_ZS_PRIM); gDPSetAlphaCompare(g++,G_AC_NONE);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPSetCombineLERP(g++,0,0,0,PRIMITIVE,0,0,0,TEXEL0,0,0,0,PRIMITIVE,0,0,0,TEXEL0);
    gDPSetPrimColor(g++,0,255,r,gcol,b,255);
    gDPLoadTextureBlock_4b(g++,af_pw_hash,G_IM_FMT_I,16,16,0,G_TX_CLAMP,G_TX_CLAMP,4,4,0,0);
    gSPTextureRectangle(g++,x*4,y*4,(x+16)*4,(y+16)*4,0,0,0,1024,1024);
    gDPPipeSync(g++); PTR(graph,0x298)=g;
}
