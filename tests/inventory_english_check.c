#include <assert.h>
#include <string.h>

int af_tag_cells(const unsigned char *, int, int);
int af_tag_load_item(unsigned char *, unsigned short);
static unsigned char widths[256];
static unsigned int seen_capacity, seen_item;
const unsigned char *af_tag_test_cuts(void) { return widths; }
int af_load_item_name(unsigned char *out, unsigned int capacity, unsigned int item) {
    seen_capacity = capacity; seen_item = item;
    if (!out || item == 0xFFFFu) return 0;
    memcpy(out, "Sixteen-byte tag", 16);
    return 1;
}
int main(void) {
    unsigned char guarded[18];
    int i;
    for (i = 0; i < 256; ++i) widths[i] = 6;
    widths['i'] = 10;
    assert(af_tag_cells((const unsigned char *)"iiii            ", 16, ' ') == 1);
    assert(af_tag_cells((const unsigned char *)"wide word       ", 16, ' ') == 5);
    assert(af_tag_cells((const unsigned char *)"                ", 16, ' ') == 0);
    assert(af_tag_cells((const unsigned char *)"1234567890123456", 16, ' ') == 8);
    assert(af_tag_cells((const unsigned char *)"          Bells ", 16, ' ') == 8);
    assert(af_tag_cells(0, 16, ' ') == 0);
    assert(af_tag_cells((const unsigned char *)"x", -1, ' ') == 0);
    assert(af_tag_cells((const unsigned char *)"x", 17, ' ') == 0);
    widths['x'] = 255;
    assert(af_tag_cells((const unsigned char *)"x", 1, ' ') == 1);
    memset(guarded, '!', sizeof(guarded));
    assert(af_tag_load_item(guarded+1, 0x2345) == 1);
    assert(seen_capacity == 16 && seen_item == 0x2345);
    assert(guarded[0] == '!' && guarded[17] == '!');
    assert(memcmp(guarded+1, "Sixteen-byte tag", 16) == 0);
    assert(af_tag_load_item(guarded+1, 0xFFFF) == 0);
    assert(memcmp(guarded+1, "Sixteen-byte tag", 16) == 0);
    return 0;
}
