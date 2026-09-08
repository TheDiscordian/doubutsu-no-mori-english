#include <string.h>

unsigned int af_departed_looks,af_departed_paper,af_departed_calls,af_departed_errors;
unsigned int af_departed_log[16];
unsigned char af_departed_fields[200],af_departed_sender[12];
float af_departed_draw;

static void event(unsigned int value) {
    if (af_departed_calls < 16u) af_departed_log[af_departed_calls] = value;
    ++af_departed_calls;
}
unsigned int af_departed_test_looks(unsigned int id) {
    event(1u);if (id < 0xE000u || id >= 0xE0D8u) ++af_departed_errors;
    return af_departed_looks;
}
float af_departed_test_random(void) { event(2u);return af_departed_draw; }
void af_departed_test_name(unsigned char *out,unsigned int id) {
    event(4u);if (id >= 216u) ++af_departed_errors;
    memcpy(out,"NATIVE",6);
}
void af_departed_test_field(unsigned int slot,const unsigned char *value,unsigned int length) {
    event(3u+slot*2u);
    if (slot >= 4u || length != 6u) { ++af_departed_errors;return; }
    memcpy(af_departed_fields+slot*10u,value,6);
    memset(af_departed_fields+slot*10u+6u,' ',4);
}
unsigned int af_departed_test_paper(void) { event(10u);return af_departed_paper; }
void af_departed_test_sender(unsigned char *out,const unsigned char *id) {
    event(11u);memcpy(af_departed_sender,id,12);
    memcpy(out,"NATIVE",6);memcpy(out+6,id+4,6);
    out[12] = id[1];out[13] = id[10];out[14] = id[2];out[15] = id[3];out[16] = 1;
}
