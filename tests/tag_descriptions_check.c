#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
extern int af_tag_description_prepare(const u8 *, const u8 *, int);
extern void af_tag_description_draw(void *, const u8 *, float, float, float, float, float);
extern void af_tag_animal(u8 *, const u8 *);
extern void af_tag_special(u8 *, unsigned short);
static u8 widths[256];
static char rows[3][40];
static unsigned int row_width[3], calls, loads, reject, quest_calls, expected_kind;
static int game;
const u8 *af_tag_test_cuts(void) { return widths; }

int af_load_display_name(u8 *out, unsigned int cap, unsigned int id) {
    const char *name = 0;
    ++loads; assert(cap == 8);
    if (reject) return 0;
    switch (id) {
        case 0xE000: name = "Portia  "; break;
        case 0xE001: name = "Kiki    "; break;
        case 0xE002: name = "Puddles "; break;
        case 0xE003: name = "Candi   "; break;
        case 0xE004: name = "Monique "; break;
        case 0xE005: name = "Whitney "; break;
        case 0xE006: name = "Friga   "; break;
        case 0xE007: name = "Baabara "; break;
        case 0xE008: name = "Purrl   "; break;
        case 0xE009: name = "Freckles"; break;
        case 0xE00A: name = "Cheri   "; break;
        case 0xE00B: name = "Octavian"; break;
        case 0xD00F: name = "Jingle  "; break;
        case 0xD008: name = "Tom Nook"; break;
        case 0xD001: name = "Redd    "; break;
        case 0xD03D: name = "Katrina "; break;
        case 0x800D: name = "Snowman "; break;
        default: return 0;
    }
    memcpy(out, name, 8); return 1;
}
void af_tag_native_animal(u8 *out, const u8 *identity) {
    (void)identity; memcpy(out, "Animal", 6);
}
void af_tag_native_special(u8 *out, unsigned short id) {
    (void)id; memcpy(out, "Native", 6);
}
int af_tag_quest_names(u8 *to, u8 *from, int index) {
    ++quest_calls; assert(index == 14);
    memcpy(to, "Freckles", 8); memcpy(from, "Tom Nook", 8); return 1;
}

float af_tag_native_draw(void *g, const u8 *s, int n, float x, float y,
                         int r, int green, int b, int a, int reverse, int cut,
                         float sx, float sy, int mode) {
    unsigned int row = (unsigned int)((y-70.0f)/12.0f), i;
    assert(g == &game && row < 3 && n > 0 && n <= 12);
    assert(y == 70.0f+row*12.0f && x == 50.0f+row_width[row]*0.75f);
    assert(sx == 0.75f && sy == 0.75f && a == 255 && !reverse && cut == 1 && !mode);
    assert((r == 90 && green == 60 && b == 50) ||
           (r == 205 && green == 40 && b == 40) ||
           (r == 100 && green == 65 && b == 195) ||
           (r == 60 && green == 150 && b == 65) ||
           (r == 165 && green == 30 && b == 255) ||
           (r == 60 && green == 50 && b == 155));
    if (r != 90) {
        const unsigned char palette[][3] = {{205,40,40}, {100,65,195}, {60,150,65},
                                             {165,30,255}, {60,50,155}};
        unsigned int colour = row == 2 ?
            (expected_kind == 3 || expected_kind == 9 ? 2 : expected_kind == 5 ? 3 :
             expected_kind == 6 || expected_kind == 7 || expected_kind == 8 ? 4 : 1) :
            expected_kind == 4 ? 2 : 0;
        assert(r == palette[colour][0] && green == palette[colour][1] && b == palette[colour][2]);
    }
    assert(strlen(rows[row])+(unsigned int)n < sizeof(rows[row]));
    strncat(rows[row], (const char *)s, (size_t)n);
    for (i = 0; i < (unsigned int)n; ++i) row_width[row] += 12-widths[s[i]];
    ++calls; return 0;
}

static void check(u8 *tag, u8 *mail, const char *a, const char *b, const char *c) {
    u8 old_tag[84], old_mail[164]; unsigned int count, before, widest, i;
    memcpy(old_tag, tag, sizeof(old_tag)); memcpy(old_mail, mail, sizeof(old_mail));
    expected_kind = tag[2];
    count = (unsigned int)af_tag_description_prepare(tag, mail, 14);
    before = loads; calls = 0;
    memset(rows, 0, sizeof(rows)); memset(row_width, 0, sizeof(row_width));
    af_tag_description_draw(&game, tag, 50, 70, 0.75f, 9, 12);
    assert(loads == before && calls >= 4 && calls <= 5);
    assert(!strcmp(rows[0], a) && !strcmp(rows[1], b) && !strcmp(rows[2], c));
    widest = 0;
    for (i = 0; i < 3; ++i) if (row_width[i] > widest) widest = row_width[i];
    widest = (widest+11)/12; if (widest < 4) widest = 4;
    assert(count == widest);
    assert(!memcmp(old_tag, tag, sizeof(old_tag)) && !memcmp(old_mail, mail, sizeof(old_mail)));
    before = calls; af_tag_description_draw(&game, old_tag, 50, 70, 0.75f, 9, 12);
    assert(calls == before); /* A different owner cannot display stale names. */
}

int main(int argc, char **argv) {
    u8 guard_tag[86], guard_mail[166], *tag = guard_tag+1, *mail = guard_mail+1;
    u8 out[10], identity[] = {0xE0, 0x0B}; unsigned int i;
    const char *senders[] = {"from Octavian", "from Jingle", "from Tom Nook", "from Redd", "from home",
                             "from Katrina", "from the HRA", "from Tom Nook", "from Snowman"};
    const u8 kind[] = {2,5,6,6,7,8,9,6,5};
    FILE *f;
    assert(argc == 2); f = fopen(argv[1], "rb"); assert(f);
    assert(fread(widths, 1, 256, f) == 256); assert(fclose(f) == 0);
    memset(guard_tag, 0xA5, sizeof(guard_tag)); memset(guard_mail, 0xA5, sizeof(guard_mail));
    memset(tag, 0, 84); memset(mail, 0, 164);
    memcpy(tag+0x44, "Native    Sender", 16);
    memcpy(mail, "Player", 6); memcpy(mail+0x12, "Sender", 6);
    mail[0x10] = mail[0x22] = 1; mail[0x0C] = 9; mail[0x1E] = 11;
    for (i = 0; i < 9; ++i) {
        mail[0x28] = (u8)i; tag[2] = kind[i];
        check(tag, mail, i == 5 ? "Freckles's" : "Letter to", i == 5 ? "fortune" : "Freckles", senders[i]);
    }
    tag[2] = 1; check(tag, mail, "Delivery for", "Freckles", "from Tom Nook"); assert(quest_calls == 1);
    tag[2] = 2; mail[0x28] = 0; mail[0x10] = mail[0x22] = 0;
    check(tag, mail, "Letter to", "Player", "from Sender");
    tag[2] = 4; mail[0x10] = 2; memcpy(mail, "\x19\x07\xF8\x11\x05\xC3", 6);
    check(tag, mail, "Letter to", "the Museum", "from Sender");
    tag[2] = 3; mail[0x10] = 0; mail[0x22] = 2;
    memcpy(mail, "Player", 6); memcpy(mail+0x12, "\x19\x07\xF8\x11\x05\xC3", 6);
    check(tag, mail, "Letter to", "Player", "from Museum");
    tag[2] = 2; mail[0x10] = mail[0x22] = 1;
    memcpy(mail+0x12, "Sender", 6);
    mail[0x0C] = 216; mail[0x1E] = 255;
    check(tag, mail, "Letter to", "Player", "from Sender");
    reject = 1; mail[0x0C] = 9; mail[0x1E] = 11;
    check(tag, mail, "Letter to", "Player", "from Sender");
    memset(out, 0xA5, sizeof(out)); af_tag_animal(out+1, identity);
    assert(!memcmp(out+1, "Animal  ", 8) && out[0] == 0xA5 && out[9] == 0xA5);
    af_tag_special(out+1, 0xD008);
    assert(!memcmp(out+1, "Native  ", 8) && out[0] == 0xA5 && out[9] == 0xA5);
    reject = 0; af_tag_animal(out+1, identity);
    assert(!memcmp(out+1, "Octavian", 8)); af_tag_special(out+1, 0xD008);
    assert(!memcmp(out+1, "Tom Nook", 8) && out[0] == 0xA5 && out[9] == 0xA5);
    assert(guard_tag[0] == 0xA5 && guard_tag[85] == 0xA5 && guard_mail[0] == 0xA5 && guard_mail[165] == 0xA5);
    puts("15 complete compositions, native spacing, full names, fallbacks, and guards passed");
    return 0;
}
