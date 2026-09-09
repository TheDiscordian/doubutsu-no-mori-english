/* Exact GameCube landmark words, with separate bounded lines. */
typedef struct { unsigned char first[8], second[8]; } AfMapLabel;
const AfMapLabel af_map_labels[6] = {
    {"Shop", ""}, {"Police", "Station"}, {"Post", "Office"},
    {"Wishing", "Well"}, {"Train", "Station"}, {"Dump", ""}
};

extern float af_map_native_draw(void *, const unsigned char *, int, float, float,
                               int, int, int, int, int, int, float, float, int);

float af_map_label_draw(void *game, const unsigned char *text, int length,
                        float x, float y, int r, int g, int b, int a,
                        int reverse, int cut, float sx, float sy, int mode) {
    int second = 0;
    float result;
    if (!text || length < 1 || length > 8) return 0.0f;
    result = af_map_native_draw(game, text, length, x, y, r, g, b, a,
                                reverse, cut, sx, sy, mode);
    while (second < 8 && text[8+second]) ++second;
    if (second)
        result = af_map_native_draw(game, text+8, second, x, y+12.0f,
                                    r, g, b, a, reverse, cut, sx, sy, mode);
    return result;
}
