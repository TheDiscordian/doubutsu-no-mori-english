#include <assert.h>
#include <string.h>
#include "extension.h"

extern void af_borrowed_catchphrase(unsigned char *, const unsigned char *);
extern unsigned int af_catchphrase_enabled, af_catchphrase_header[8], af_catchphrase_dma_error;
extern unsigned char af_catchphrase_rows[216*16], af_catchphrase_animal[0x528];
extern const unsigned char *af_catchphrase_test_animal(const unsigned char *);
static af_u32 words[2];
static int ready, initials, writes, invalidates;
static unsigned char actor[0x178], saved_actor[0x178], saved_animal[0x528];
static const unsigned char key[4] = {0xD0, 0x90, ' ', ' '};

af_u32 *af_borrowed_test_word(af_u32 at) {
    assert(at == 0x801953C4u || at == 0x801953C8u);
    return words+(at-0x801953C4u)/4;
}
const unsigned char *af_borrowed_test_animal(const unsigned char *a) {
    return af_catchphrase_test_animal(a);
}
int af_text_names_init(void) {++initials; return ready;}
void af_writeback(void *at, unsigned int length) {
    assert((__UINTPTR_TYPE__)at == 0x801953C4u && length == 4); ++writes;
}
void af_invalidate(void *at, unsigned int length) {
    assert((__UINTPTR_TYPE__)at == 0x801953C4u && length == 4); ++invalidates;
}
static void resolve(const unsigned char *a, const unsigned char expected[10]) {
    unsigned char out[12]; memset(out,'!',sizeof out);
    memcpy(saved_actor,actor,sizeof actor); memcpy(saved_animal,af_catchphrase_animal,sizeof saved_animal);
    af_borrowed_catchphrase(out+1,a);
    assert(out[0] == '!' && out[11] == '!' && !memcmp(out+1,expected,10));
    assert(!memcmp(saved_actor,actor,sizeof actor) && !memcmp(saved_animal,af_catchphrase_animal,sizeof saved_animal));
    assert(!af_catchphrase_dma_error);
}
int main(void) {
    unsigned char fallback[10]; memset(fallback,' ',10);memcpy(fallback,key,4);
    memset(af_catchphrase_rows,' ',sizeof af_catchphrase_rows);
    for (unsigned int i=0;i<216;++i) {
        unsigned char *r=af_catchphrase_rows+i*16;
        r[0]=0xF0; r[1]=0; r[2]=0; r[3]=(unsigned char)i;
        r[4]=0xE0; r[5]=(unsigned char)i;memcpy(r+6,"ordinary  ",10);
    }
    memcpy(af_catchphrase_rows,key,4);af_catchphrase_rows[5]=0x14;
    memcpy(af_catchphrase_rows+6,"zzzzzz    ",10);
    memcpy(af_catchphrase_rows+16,key,4);af_catchphrase_rows[21]=0xC5;
    memcpy(af_catchphrase_rows+22,"bingo     ",10);
    actor[2]=3;actor[0x177]=1;af_catchphrase_animal[0]=0xE0;
    memcpy(af_catchphrase_animal+0x4E5,key,4);
    for (unsigned int i=0;i<216;++i) {
        af_catchphrase_animal[1]=(unsigned char)i;
        resolve(actor,(const unsigned char *)(i == 0xC5 ? "bingo     " : "zzzzzz    "));
    }
    af_catchphrase_animal[1]=2;af_catchphrase_enabled=0;resolve(actor,fallback);
    af_catchphrase_enabled=1;af_catchphrase_header[0]^=1;resolve(actor,fallback);af_catchphrase_header[0]^=1;
    af_catchphrase_animal[0]=0xDF;resolve(actor,fallback);
    af_catchphrase_animal[0]=0xE0;af_catchphrase_animal[1]=216;resolve(actor,fallback);
    af_catchphrase_animal[1]=2;memcpy(af_catchphrase_animal+0x4E5,"Yup!",4);
    resolve(actor,(const unsigned char *)"Yup!      ");
    memcpy(af_catchphrase_animal+0x4E5,af_catchphrase_rows+32,4);
    resolve(actor,(const unsigned char *)"ordinary  ");
    actor[0x177]=0;resolve(actor,(const unsigned char *)"none      ");
    actor[0x177]=1;actor[2]=2;resolve(actor,(const unsigned char *)"none      ");
    resolve(0,(const unsigned char *)"          ");af_borrowed_catchphrase(0,actor);
    assert(!af_text_extension_init() && !initials && !writes);
    words[0]=0x0C065487;assert(!af_text_extension_init() && !initials && !writes);
    words[1]=0x02C02025;assert(!af_text_extension_init() && initials == 1 && !writes);
    assert(words[0] == 0x0C065487 && words[1] == 0x02C02025);
    ready=1;assert(af_text_extension_init() && initials == 2 && writes == 1 && invalidates == 1);
    assert(words[0] >> 26 == 3 && words[1] == 0x02C02025);
    assert(!af_text_extension_init() && initials == 2 && writes == 1);
    return 0;
}
