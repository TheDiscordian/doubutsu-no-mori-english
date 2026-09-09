/* Complete transient world labels; the native 40-byte state stays unchanged. */
#include "names.h"
#include "font.h"

static unsigned char world_name[16];
static int world_pixels;
static const unsigned char unavailable[] = "Name unavailable";

#ifdef __mips__
#define native_zero ((void (*)(void *, int))0x8002F4C0u)
#define native_name ((void (*)(unsigned char *, unsigned short))0x80096740u)
#define full_name ((int (*)(unsigned char *, unsigned int, unsigned int))0x801969C8u)
#define native_draw ((float (*)(void *, const unsigned char *, int, float, float, \
                    int, int, int, int, int, int, float, float, int))0x80090E98u)
static float *state(void) { return (float *)0x801446A0u; }
#else
extern void native_zero(void *, int);
extern void native_name(unsigned char *, unsigned short);
extern int full_name(unsigned char *, unsigned int, unsigned int);
extern float native_draw(void *, const unsigned char *, int, float, float,
                         int, int, int, int, int, int, float, float, int);
extern float *state(void);
#endif

void af_world_reset(void *destination, int bytes) {
    int i;
    native_zero(destination, bytes);
    for (i = 0; i < 16; ++i) world_name[i] = ' ';
    world_pixels = 0;
}

void af_world_load(unsigned char *destination, unsigned short item) {
    int i;
    native_name(destination, item); /* Exactly ten compatibility bytes. */
    if (!full_name(world_name, sizeof(world_name), item))
        for (i = 0; i < 16; ++i) world_name[i] = unavailable[i];
}

void af_world_measure(void) {
    int length = 16;
    float scale;
    while (length && world_name[length-1] == ' ') --length;
    world_pixels = af_glyph_string_width(world_name, (unsigned int)length);
    /* The N64 mesh uses (twelve-pixel cells - 2) / 8. Replace cell count
       with measured width, retaining its geometry and a nonnegative minimum. */
    scale = ((float)world_pixels / 12.0f - 2.0f) / 8.0f;
    state()[5] = scale < 0.0f ? 0.0f : scale;
}

float af_world_draw(void *game, const unsigned char *native, int length,
                    float x, float y, int r, int g, int b, int a,
                    int reverse, int cut, float scale_x, float scale_y, int mode) {
    (void)native; (void)length; (void)x;
    /* Centre the complete proportional line on the unchanged native bubble.
       Keep the supplied vertical position, alpha, scale, and drawing mode. */
    x = state()[0] + 160.0f - (float)world_pixels * scale_x * 0.5f;
    return native_draw(game, world_name, 16, x, y, r, g, b, a,
                       reverse, cut, scale_x, scale_y, mode);
}
