#include "item_article.h"
#include "../../runtime/item_name.h"
#include "../../runtime/crc32.h"

extern const unsigned char af_item_article_data[AF_ITEM_ARTICLE_BYTES];

#ifdef __mips__
static unsigned int convert(unsigned int item) {
    return ((unsigned short (*)(unsigned short))0x800BF10Cu)((unsigned short)item);
}
#else
extern unsigned int af_article_test_convert(unsigned int);
#define convert af_article_test_convert
#endif

int af_notice_item_article(unsigned int item, const unsigned char *name) {
    const unsigned char *entry;
    unsigned int crc;
    int index;
    if (!name || !item || item > 65535u) return -1;
    index = af_item_name_index(convert(item));
    if (index < 0) return -1;
    if (index >= 756) index = 756+(index-756)/4;
    if (index >= 1703) return -1;
    entry = af_item_article_data+48u+5u*(unsigned int)index;
    if (entry[0] > 4u) return -1;
    crc = ((unsigned int)entry[1]<<24)|((unsigned int)entry[2]<<16)
        |((unsigned int)entry[3]<<8)|entry[4];
    return af_crc32(name, 16u) == crc ? entry[0] : -1;
}
