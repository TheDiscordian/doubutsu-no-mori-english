/* Complete fixed secret letters in the conversation overlay's own lifetime. */
extern const unsigned char af_secret_templates[600];

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

int af_secret_create(unsigned char *mail,unsigned int *selected,
                     unsigned int choice,unsigned int *capital) {
    unsigned int i;
    const unsigned char *row;
    if (!valid(mail,132u) || !valid(selected,4u) || !valid(capital,4u)
            || ((__UINTPTR_TYPE__)mail&1u) || ((__UINTPTR_TYPE__)selected&3u)
            || ((__UINTPTR_TYPE__)capital&3u) || choice >= 15u
            || overlap(mail,132u,selected,4u) || overlap(mail,132u,capital,4u)
            || overlap(selected,4u,capital,4u)
            || overlap(mail,132u,af_secret_templates,600u)
            || overlap(selected,4u,af_secret_templates,600u)
            || overlap(capital,4u,af_secret_templates,600u)) return 0;
    if (*capital > 1u) return 0;
    row = af_secret_templates+(choice*2u+*capital)*20u;
    /* All fallible checks precede publication. Preserve paper, gift, and the
     * five trailing date/padding bytes. The wrapper selects paper and clears
     * selected memory only after success, in the original native order.
     */
    mail[0] = 0;mail[4] = 128u;
    for (i = 0; i < 122u; ++i) mail[5u+i] = i < 16u ? row[4u+i] : 0;
    *capital = row[2];
    return 1;
}
