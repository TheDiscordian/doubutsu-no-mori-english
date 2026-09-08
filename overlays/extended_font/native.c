/* Native ABI adapters; exercised only by the isolated extended-font probe. */
#include "font.h"

struct Character {
    const unsigned char *text;
    unsigned char bytes, flags;
};
struct Data {
    int loaded, id, length, cut;
    unsigned char text[1024];
};
struct Window {
    unsigned char prefix[12];
    const struct Data *data;
};
typedef char char_bytes_offset[__builtin_offsetof(struct Character,bytes)==4 ? 1 : -1];
typedef char char_flags_offset[__builtin_offsetof(struct Character,flags)==5 ? 1 : -1];
typedef char window_data_offset[__builtin_offsetof(struct Window,data)==12 ? 1 : -1];

void af_glyph_draw_char(struct Character *character, void *graph, void *display) {
    unsigned int previous = af_glyph_begin(character->text, character->bytes);
    void (*draw)(void *,void *,void *) = character->flags&2u
        ? (void *)0x800917C8u : (void *)0x8009167Cu;
    draw(character,graph,display);
    af_glyph_end(previous);
}

int af_glyph_skip_tag(const struct Window *window,int index) {
    const struct Data *data = window->data;
    if (!data || index<0 || data->length<0 || data->length>1024 || index>=data->length) return 0;
    return data->text[index]==0x80u
        && af_glyph_index(data->text+index,(unsigned int)(data->length-index))<0;
}
