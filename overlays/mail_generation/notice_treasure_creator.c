#include "notice_treasure_creator.h"
#include "../../runtime/notice/treasure.h"
#include "../../runtime/item_name.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define town ((const unsigned char *)0x80129E00u)
#else
extern const unsigned char af_notice_treasure_test_town[6];
#define town af_notice_treasure_test_town
#endif

int af_notice_treasure_create(AfNpcMailCreateWork *work, unsigned char *destination,
                               AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailSession *session;
    AfMailCapture *capture;
    AfMailRecord *record;
    AfMailField name;
    const unsigned char *request, *animal;
    unsigned int i, j, number, npc, item, mask;
    unsigned char text[16], coordinate;
    if (!af_mail_create_guard(work, destination, active, capital, town, 6u)) return 0;
    session = &work->captured.session;
    request = session->animal;
    if (!request || session->remail)
        return af_quest_reply_mail_create(work, destination, active, capital);
    if ((__UINTPTR_TYPE__)request & 1u) return 0;
    if (request[11] != 245u)
        return af_quest_reply_mail_create(work, destination, active, capital);
    animal = session->player;
    if (!animal || ((__UINTPTR_TYPE__)animal & 1u) || session->condition || session->foreign
            || request[0] != 'A' || request[1] != 'F' || request[2] != 'N' || request[3] != 'T'
            || request[8] < 1u || request[8] > 6u || request[9] < 1u || request[9] > 5u
            || request[10] > 4u || animal[11] >= 6u) return 0;
    number = ((unsigned int)request[4] << 8) | request[5];
    item = ((unsigned int)request[6] << 8) | request[7];
    npc = ((unsigned int)animal[0] << 8) | animal[1];
    mask = af_notice_treasure_mask(number);
    if (!mask || (number-0x1F0u)/3u != animal[11] || !item || npc < 0xE000u || npc >= 0xE0D8u) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    capture = &work->captured.capture;
    capture->capital = *capital;
    if (mask & (1u << 1)) {
        if (!af_npc_mail_sources_init(&work->captured.sources, af_npc_word_data, AF_NPC_WORD_BYTES,
                                      af_npc_alias_data, AF_NPC_ALIAS_BYTES)
                || !af_npc_mail_source_name(&name, &work->captured.sources, npc)
                || !af_mail_capture_set(capture, 1u, name.text, name.length, 0u)) return 0;
    }
    if ((mask & (1u << 2)) && (!af_load_item_name(text, 16u, item)
            || !af_mail_capture_set(capture, 2u, text, 16u, request[10]))) return 0;
    coordinate = (unsigned char)('0'+request[8]);
    if ((mask & (1u << 3)) && !af_mail_capture_set(capture, 3u, &coordinate, 1u, 0u)) return 0;
    coordinate = (unsigned char)('0'+request[9]);
    if ((mask & (1u << 4)) && !af_mail_capture_set(capture, 4u, &coordinate, 1u, 0u)) return 0;
    if ((mask & (1u << 5)) && !af_mail_capture_set(capture, 5u, town, 6u, 0u)) return 0;
    record = &work->generation.catalog.record;
    record->catalog = AF_MAIL_GLYPH_CATALOG_ID;
    record->flags = (unsigned char)*capital;
    record->field_mask = mask;
    record->templates[0] = (unsigned short)number;
    for (i = 1; i <= 5u; ++i)
        if (mask & (1u << i))
            for (j = 0; j < sizeof(AfMailField); ++j)
                ((unsigned char *)&record->fields[i])[j] = ((const unsigned char *)&capture->fields[i])[j];
    if (!af_notice_treasure_pack(work->stage, 96u, record)
            || !af_notice_treasure_decode_parts(&work->generation.catalog, &work->generation.text,
                                                work->generation.wire, work->stage, 96u)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->generation.text.final_capital;
    return 1;
}
