/* Select the complete default without rewriting any saved/custom message. */
extern const unsigned char af_gyroid_native_default[64];

unsigned int af_gyroid_default_select(unsigned int requested, const unsigned char *message) {
    unsigned int i;
    if (requested != 0x0928u || !message)
        return requested;
    for (i = 0; i < 64; ++i)
        if (message[i] != af_gyroid_native_default[i])
            return requested;
    return 0x2AE7u;
}
