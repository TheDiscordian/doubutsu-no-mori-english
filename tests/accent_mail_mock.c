/* Isolated cartridge adapter for immutable catalogues two through five. */
#include <string.h>
#include "../overlays/accent_mail/accent_mail.h"

unsigned char af_mail_catalog_rom[0x200000];
unsigned int af_mail_catalog_reads, af_mail_catalog_fail_read, af_mail_catalog_dma_error;
unsigned int af_accent_test_hooks[8], af_accent_test_world_calls, af_accent_test_world_ok=1, af_accent_test_flushes;
volatile unsigned int *af_accent_test_word(unsigned int address) {
    switch (address) {
        case 0x80197654u:return af_accent_test_hooks;
        case 0x80196C28u:return af_accent_test_hooks+2;
        case 0x80196B34u:return af_accent_test_hooks+4;
        case 0x801992A8u:return af_accent_test_hooks+6;
        default:return 0;
    }
}
void af_accent_test_flush(void) { ++af_accent_test_flushes; }
int af_world_font_install(void) { ++af_accent_test_world_calls;return af_accent_test_world_ok; }
unsigned int af_mail_catalog_test_installed(void) { return 1; }
unsigned int af_mail_catalog_workspace_size(void) { return sizeof(AfMailWorkspace); }
int af_mail_view_test_width(unsigned char code) { return code == 0x7F ? 0 : 6; }

int af_mail_catalog_test_dma(void *destination,unsigned int source,unsigned int size) {
    unsigned int base,limit,local,i;
    unsigned char *out=destination;
    ++af_mail_catalog_reads;
    base=source>=AF_ACCENT_CATALOG_VROM ? AF_ACCENT_CATALOG_VROM :
        source>=AF_MAIL_GLYPH_CATALOG_VROM ? AF_MAIL_GLYPH_CATALOG_VROM :
        source>=AF_MAIL_FORTUNE_CATALOG_VROM ? AF_MAIL_FORTUNE_CATALOG_VROM : AF_MAIL_CATALOG_VROM;
    limit=base==AF_ACCENT_CATALOG_VROM ? AF_ACCENT_CATALOG_BYTES :
        base==AF_MAIL_GLYPH_CATALOG_VROM ? AF_MAIL_GLYPH_CATALOG_BYTES :
        base==AF_MAIL_FORTUNE_CATALOG_VROM ? AF_MAIL_FORTUNE_CATALOG_BYTES : AF_MAIL_CATALOG_BYTES;
    if (source<base || source-base>limit || size>limit-(source-base)
            || ((__UINTPTR_TYPE__)destination&15u) || (source&15u) || (size&15u)) {
        ++af_mail_catalog_dma_error;
        return 0;
    }
    if (af_mail_catalog_reads==af_mail_catalog_fail_read) {
        if (size) out[0]=0xEE;
        return 0;
    }
    local=source-base;
    if (local<78112u) {
        unsigned int *words=destination;
        for (i=0;i<size;i+=4) {
            const unsigned char *p=af_mail_catalog_rom+source-AF_MAIL_CATALOG_VROM+i;
            words[i/4]=((unsigned int)p[0]<<24)|((unsigned int)p[1]<<16)|((unsigned int)p[2]<<8)|p[3];
        }
    } else memcpy(destination,af_mail_catalog_rom+source-AF_MAIL_CATALOG_VROM,size);
    return 1;
}
