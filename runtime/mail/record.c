#include "record.h"

static unsigned int crc16(const unsigned char *data, unsigned int size) {
    unsigned int crc = 0xFFFFu, i, bit;
    for (i = 0; i < size; ++i) {
        crc ^= (unsigned int)data[i] << 8;
        for (bit = 0; bit < 8; ++bit)
            crc = ((crc << 1) ^ ((crc & 0x8000u) ? 0x1021u : 0u)) & 0xFFFFu;
    }
    return crc;
}

static void put16(unsigned char *output, unsigned int value) {
    output[0] = (unsigned char)(value >> 8);
    output[1] = (unsigned char)value;
}

static unsigned int get16(const unsigned char *input) {
    return ((unsigned int)input[0] << 8) | input[1];
}

int af_mail_record_pack(unsigned char *output, unsigned int capacity, const AfMailRecord *record) {
    unsigned char data[AF_MAIL_RECORD_BYTES];
    unsigned int i, j, parts, pos;
    if (!output || !record || capacity < AF_MAIL_RECORD_BYTES || !record->catalog
        || record->kind > 1 || record->reserved || record->field_mask >> AF_MAIL_FIELD_COUNT)
        return 0;
    parts = record->kind ? 5u : 1u;
    pos = 8 + 2*parts;
    for (i = 0; i < AF_MAIL_FIELD_COUNT; ++i) {
        const AfMailField *field = &record->fields[i];
        if (record->field_mask & (1u << i)) {
            if (field->length > AF_MAIL_FIELD_BYTES || field->article > 4)
                return 0;
            pos += 1 + field->length;
        }
    }
    if (pos + 2 > AF_MAIL_RECORD_BYTES)
        return 0;
    for (i = 0; i < AF_MAIL_RECORD_BYTES; ++i)
        data[i] = 0;
    data[0] = 0xAF;
    data[1] = (unsigned char)(0x10u | record->kind);
    data[2] = (unsigned char)(pos + 2);
    put16(data + 3, record->catalog);
    data[5] = (unsigned char)(record->field_mask >> 16);
    data[6] = (unsigned char)(record->field_mask >> 8);
    data[7] = (unsigned char)record->field_mask;
    pos = 8;
    for (i = 0; i < parts; ++i) {
        put16(data + pos, record->templates[i]);
        pos += 2;
    }
    for (i = 0; i < AF_MAIL_FIELD_COUNT; ++i) {
        const AfMailField *field = &record->fields[i];
        if (record->field_mask & (1u << i)) {
            data[pos++] = (unsigned char)((field->article << 5) | field->length);
            for (j = 0; j < field->length; ++j)
                data[pos++] = field->text[j];
        }
    }
    put16(data + pos, crc16(data, pos));
    /* Staging preserves overlapping source/destination and makes failure atomic. */
    for (i = 0; i < AF_MAIL_RECORD_BYTES; ++i)
        output[i] = data[i];
    return 1;
}

int af_mail_record_unpack(AfMailRecord *record, const unsigned char *input,
                          unsigned int size, unsigned int expected_catalog) {
    AfMailRecord value;
    unsigned int i, j, used, parts, pos;
    unsigned char *value_bytes = (unsigned char *)&value;
    if (!record || !input || size != AF_MAIL_RECORD_BYTES || !expected_catalog
        || expected_catalog > 0xFFFFu || input[0] != 0xAF
        || (input[1] != 0x10 && input[1] != 0x11))
        return 0;
    used = input[2];
    parts = input[1] == 0x11 ? 5u : 1u;
    if (used < 10 + 2*parts || used > AF_MAIL_RECORD_BYTES || (input[5] & 0xF0)
        || get16(input + 3) != expected_catalog)
        return 0;
    for (i = used; i < AF_MAIL_RECORD_BYTES; ++i)
        if (input[i])
            return 0;
    if (get16(input + used - 2) != crc16(input, used - 2))
        return 0;
    for (i = 0; i < sizeof(value); ++i)
        value_bytes[i] = 0;
    value.kind = input[1] & 1;
    value.catalog = (unsigned short)expected_catalog;
    value.field_mask = ((unsigned int)input[5] << 16) | ((unsigned int)input[6] << 8) | input[7];
    pos = 8;
    for (i = 0; i < parts; ++i) {
        value.templates[i] = (unsigned short)get16(input + pos);
        pos += 2;
    }
    for (i = 0; i < AF_MAIL_FIELD_COUNT; ++i) {
        AfMailField *field = &value.fields[i];
        if (value.field_mask & (1u << i)) {
            if (pos >= used - 2)
                return 0;
            field->length = input[pos] & 31;
            field->article = input[pos++] >> 5;
            if (field->length > AF_MAIL_FIELD_BYTES || field->article > 4
                || pos + field->length > used - 2)
                return 0;
            for (j = 0; j < field->length; ++j)
                field->text[j] = input[pos++];
        }
    }
    if (pos != used - 2)
        return 0;
    for (i = 0; i < sizeof(value); ++i)
        ((unsigned char *)record)[i] = value_bytes[i];
    return 1;
}
