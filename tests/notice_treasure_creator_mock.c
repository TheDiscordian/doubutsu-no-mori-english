const unsigned char af_notice_treasure_test_town[6] = {'T', 'o', 'w', 'n', ' ', ' '};
int af_notice_test_article = 1;
unsigned int af_notice_test_article_calls;
extern unsigned char af_event_card_item_name[16];
int af_notice_item_article(unsigned int item, const unsigned char *name) {
    unsigned int i;
    ++af_notice_test_article_calls;
    if (item != 0x11FCu || !name) return -1;
    for (i = 0; i < 16u; ++i) if (name[i] != af_event_card_item_name[i]) return -1;
    return af_notice_test_article;
}
