unsigned int af_article_test_convert(unsigned int item) {
    if (item >= 0x17ACu && item < 0x1BA8u) return 0x2400u+((item-0x17ACu)>>2);
    if (item >= 0x1BA8u && item < 0x1C28u) return 0x2D00u+((item-0x1BA8u)>>2);
    if (item >= 0x1C28u && item < 0x1CA8u) return 0x2300u+((item-0x1C28u)>>2);
    if (item >= 0x1CA8u && item < 0x1D28u) return 0x2204u+((item-0x1CA8u)>>2);
    return item;
}
unsigned int af_item_test_convert(unsigned int item) { return af_article_test_convert(item); }
unsigned int af_item_test_installed(void) { return 0; }
void af_item_test_dma(void *destination, unsigned int source, unsigned int size) {
    (void)destination; (void)source; (void)size;
}
