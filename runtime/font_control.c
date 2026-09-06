/* English SPACE control in the native sentence renderer; no font asset changes. */
typedef unsigned char u8;

struct FontSentence {
    const u8 *text;
    u8 before_index[0x2C-4];
    int index;
    float offset, width;
    u8 before_character_scale[0x68-0x38];
    float character_scale_x;
};

typedef char check_index[__builtin_offsetof(struct FontSentence, index) == 0x2C ? 1 : -1];
typedef char check_width[__builtin_offsetof(struct FontSentence, width) == 0x34 ? 1 : -1];
typedef char check_scale[__builtin_offsetof(struct FontSentence, character_scale_x) == 0x68 ? 1 : -1];
typedef void (*SentenceControl)(struct FontSentence *, void *);

static void af_font_space(struct FontSentence *sentence, void *display_list) {
    (void)display_list;
    sentence->width += sentence->text[sentence->index+2] * sentence->character_scale_x;
}

SentenceControl af_sentence_control(unsigned command) {
    switch (command) {
        case 0x52: return (SentenceControl)0x80091900u;
        case 0x53: return (SentenceControl)0x8009193Cu;
        case 0x5A: return (SentenceControl)0x80091980u;
        case 0x67: return af_font_space;
        default: return (SentenceControl)0;
    }
}
