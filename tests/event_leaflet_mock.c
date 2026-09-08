/* Isolated equivalents of the native full-name and mode-two receipt imports. */
#include <string.h>
#include "../overlays/mail_generation/event_leaflet.h"

unsigned char af_event_test_destination[168];
unsigned int af_event_test_loads, af_event_test_receipts, af_event_test_fail_load;
unsigned int af_event_test_fail_receipt, af_event_test_bad_mode;
unsigned int af_event_test_ids[3];

unsigned int af_event_test_work_size(void) { return sizeof(AfEventLeafletWork); }

int af_load_item_name(unsigned char *out, unsigned int size, unsigned int item) {
    unsigned int i, index = af_event_test_loads++;
    if (index < 3u) af_event_test_ids[index] = item;
    if (size != 16u || af_event_test_fail_load == index+1u) return 0;
    for (i = 0; i < 16u; ++i) out[i] = (unsigned char)('A'+(item+i)%26u);
    return 1;
}

void af_event_leaflet_clear_mail(unsigned char *mail) {
    memset(mail,0,164u);
    memset(mail,' ',12u); memset(mail+12,255,4u); mail[16] = 255;
    memset(mail+18,' ',12u); memset(mail+30,255,4u); mail[34] = 255;
    mail[38] = 255; memset(mail+42,' ',122u);
}

int af_event_leaflet_receipt(unsigned char *mail, unsigned int mode) {
    if (mode != 2u) { ++af_event_test_bad_mode; return 0; }
    ++af_event_test_receipts;
    if (af_event_test_fail_receipt) return 0;
    memcpy(af_event_test_destination,mail,164u);
    af_event_test_destination[164] = af_event_test_destination[165] = 0;
    return 1;
}
