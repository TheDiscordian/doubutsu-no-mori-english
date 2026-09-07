#include <string.h>
#include "../runtime/mail/reader.h"

unsigned int af_mail_reader_buttons, af_mail_reader_copies;
void af_mail_reader_test_copy(unsigned char *destination, const unsigned char *source) {
    ++af_mail_reader_copies;
    memcpy(destination, source, 164);
}
unsigned int af_mail_reader_test_trigger(void) { return af_mail_reader_buttons; }
void af_mail_reader_test_reset(void) { memset(&af_mail_reader, 0, sizeof(af_mail_reader)); }
