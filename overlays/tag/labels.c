/* Pixel-aware native tag dimensions; no change to text or saved structures. */
#ifdef __mips__
static const unsigned char *cuts(void) {
    return (const unsigned char *)0x80106AF4u;
}
#else
extern const unsigned char *af_tag_test_cuts(void);
#define cuts af_tag_test_cuts
#endif

int af_tag_cells(const unsigned char *text, int length, int padding) {
    unsigned int width = 0, used = 0;
    const unsigned char *table = cuts();
    int i;
    if (!text || length < 0 || length > 16) return 0;
    for (i = 0; i < length; ++i) {
        unsigned int cut = table[text[i]];
        /* Unknown/corrupt metrics must not create an unsigned underflow. */
        width += cut <= 12u ? 12u-cut : 12u;
        if (text[i] != padding) used = width;
    }
    return (int)((used+11u)/12u);
}

extern int af_load_item_name(unsigned char *, unsigned int, unsigned int);
int af_tag_load_item(unsigned char *destination, unsigned short item) {
    return af_load_item_name(destination, 16u, item);
}
