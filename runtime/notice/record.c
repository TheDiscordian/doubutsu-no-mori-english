#include "record.h"

int af_notice_record_tagged(const unsigned char *input, unsigned int size) {
    return input && size >= 3u && input[0] == 0x7Fu
        && input[1] == 'B' && input[2] == 'N';
}

int af_notice_record_pack(unsigned char *output, unsigned int capacity,
                           const AfMailRecord *record) {
    unsigned char wire[AF_MAIL_RECORD_BYTES];
    unsigned int i;
    if (!output || !record || capacity < AF_NOTICE_RECORD_BYTES || record->kind
            || !af_mail_record_pack(wire, sizeof(wire), record)
            || wire[2] > AF_NOTICE_PAYLOAD_BYTES)
        return 0;
    output[0] = 0x7Fu;
    output[1] = 'B';
    output[2] = 'N';
    output[3] = 1u;
    for (i = 0; i < AF_NOTICE_PAYLOAD_BYTES; ++i)
        output[4u+i] = wire[i];
    return 1;
}

int af_notice_record_expand(unsigned char *output, unsigned int capacity,
                             const unsigned char *input, unsigned int size,
                             unsigned int expected_catalog) {
    unsigned char wire[AF_MAIL_RECORD_BYTES];
    AfMailRecord record;
    unsigned int i;
    if (!output || capacity < AF_MAIL_RECORD_BYTES || size != AF_NOTICE_RECORD_BYTES
            || !af_notice_record_tagged(input, size) || input[3] != 1u)
        return 0;
    for (i = 0; i < AF_MAIL_RECORD_BYTES; ++i)
        wire[i] = i < AF_NOTICE_PAYLOAD_BYTES ? input[4u+i] : 0;
    if (wire[2] > AF_NOTICE_PAYLOAD_BYTES
            || !af_mail_record_unpack(&record, wire, sizeof(wire), expected_catalog)
            || record.kind)
        return 0;
    for (i = 0; i < AF_MAIL_RECORD_BYTES; ++i)
        output[i] = wire[i];
    return 1;
}
