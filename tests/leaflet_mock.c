#include "../overlays/mail_generation/leaflet.h"

unsigned int af_leaflet_test_work_size(void) { return sizeof(AfLeafletWork); }
unsigned int af_leaflet_test_text_offset(void) {
    return __builtin_offsetof(AfLeafletWork,generation) +
        __builtin_offsetof(AfMailGenerateWork,text);
}
