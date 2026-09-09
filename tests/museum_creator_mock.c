#include <string.h>

unsigned int af_museum_sender_calls;

void af_museum_creator_test_sender(unsigned char *out) {
    static const unsigned char canonical[6] = {0x19,0x07,0xF8,0x11,0x05,0xC3};
    ++af_museum_sender_calls;
    memcpy(out,canonical,6);memset(out+6,' ',6);memset(out+12,255,4);out[16] = 2;
}
