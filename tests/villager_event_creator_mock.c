#include <string.h>

const unsigned char af_event_card_town[6] = {'H','E','R','E',' ',' '};
unsigned int af_event_card_item_calls,af_event_card_item_id,af_event_card_item_fail;
unsigned char af_event_card_item_name[16];

int af_load_item_name(unsigned char *out,unsigned int capacity,unsigned int item) {
    ++af_event_card_item_calls;af_event_card_item_id = item;
    if (capacity != 16u || af_event_card_item_fail) return 0;
    memcpy(out,af_event_card_item_name,16);return 1;
}
