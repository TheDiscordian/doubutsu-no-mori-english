#include "snowman_creator.h"

static int valid(const void *object,unsigned int size) {
    __UINTPTR_TYPE__ address = (__UINTPTR_TYPE__)object;
#ifdef __mips__
    return address >= 0x80000000u && address <= 0x80400000u-size;
#else
    return address >= 4096u && address <= ~(__UINTPTR_TYPE__)0-size;
#endif
}

static int overlap(const void *a,unsigned int as,const void *b,unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a,bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

int af_snowman_create(unsigned char *mail,const unsigned char *player,
                       unsigned int choice,unsigned int *capital) {
    unsigned int i;
    const unsigned char *row;
    if (!valid(mail,164u) || !valid(player,16u) || !valid(capital,4u)
            || ((__UINTPTR_TYPE__)mail&1u) || ((__UINTPTR_TYPE__)player&1u)
            || ((__UINTPTR_TYPE__)capital&3u) || choice >= AF_SNOWMAN_CHOICES
            || overlap(mail,164u,player,16u) || overlap(mail,164u,capital,4u)
            || overlap(player,16u,capital,4u)
            || overlap(mail,164u,af_snowman_templates,AF_SNOWMAN_TABLE_BYTES)
            || overlap(player,16u,af_snowman_templates,AF_SNOWMAN_TABLE_BYTES)
            || overlap(capital,4u,af_snowman_templates,AF_SNOWMAN_TABLE_BYTES)) return 0;
    if (*capital > 1u) return 0;
    row = af_snowman_templates+(choice*2u+*capital)*AF_SNOWMAN_ROW_BYTES;
    /* The selected immutable row is complete. No fallible operation follows
     * the first destination write. Match the original cleared native metadata.
     */
    for (i = 0; i < 164u; ++i) mail[i] = 0;
    for (i = 0; i < 16u; ++i) mail[i] = player[i];
    for (i = 18u; i < 30u; ++i) mail[i] = ' ';
    for (i = 30u; i < 35u; ++i) mail[i] = 255u;
    mail[36] = row[0];mail[37] = row[1];mail[39] = 128u;mail[40] = 8u;mail[41] = 12u;
    for (i = 0; i < 32u; ++i) mail[42u+i] = row[4u+i];
    *capital = row[2];
    return 1;
}
