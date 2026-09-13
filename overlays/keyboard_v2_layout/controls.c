/* N64 button colours, shapes, bindings, and animated poses are retained. */
struct af_v2_icon {
    unsigned int texture, pressed, mask;
    unsigned short button;
    unsigned char width, height;
    unsigned short x, y;
    unsigned char w, h, mirror, yellow;
};

static const struct af_v2_icon af_v2_icons[] = {
    {0xD648,0xD648,0,0,64,64,14,154,48,48,0,0},
    {0x8E48,0x8648,0,0x20,64,32,48,118,18,9,1,0},
    {0xCE48,0xC648,0,0x2000,32,64,182,115,9,18,0,0},
    {0x14648,0x16448,0x14E48,0x8000,32,32,242,121,14,14,0,0},
    {0x13E48,0x15C48,0x14E48,0x4000,32,32,254,143,14,14,0,0},
    {0x8E48,0x8648,0,0x10,64,32,102,209,18,9,0,0},
    {0x13648,0x15448,0x14E48,0x1000,32,32,170,204,14,14,0,0},
    {0x6348,0x6248,0,0x8,16,16,261,166,10,10,0,1},
    {0x6148,0x6048,0,0x2,16,16,251,176,10,10,0,1},
    {0x5F48,0x5E48,0,0x1,16,16,271,176,10,10,0,1},
    {0x6548,0x6448,0,0x4,16,16,261,186,10,10,0,1},
};

/* The shared icon renderer is generated from the verified V2 implementation. */
#include "icons.inc"

static void af_v2_labels(void *graph, void *game, float dx, float dy) {
    static const struct {const char *word; unsigned short x,y;} labels[]={
        {"Case",69,116},{"Page",195,117},{"Move",23,200},{"Cursor",251,201},
        {"Type",260,121},{"Del",272,143},{"Space",123,205},{"Done",187,205}
    };
    static const struct {
        unsigned short button,x2;
        unsigned char y,colour;
        char glyph[2];
    } letters[]={
        {0x20,107,115,0,"L"},{0x10,215,206,0,"R"},
        {0x8000,493,121,1,"A"},{0x4000,518,143,1,"B"}
    };
    unsigned int i,held=af_grid_get_button();
    for (i=0;i<sizeof(labels)/sizeof(labels[0]);++i)
        label(graph,game,labels[i].word,labels[i].x+dx,labels[i].y-dy);
    for (i=0;i<sizeof(letters)/sizeof(letters[0]);++i)
        text(graph,game,(const unsigned char *)letters[i].glyph,1,letters[i].x2*0.5f+dx,
             letters[i].y-dy+!!(held&letters[i].button),letters[i].colour,0,
             letters[i].colour ? 0.65f : 0.6f);
}
