/* Exercise the installed roster data through the actual text and alias code. */
#define AF_V3_IMPORTED_OUTFIT_SOURCE 1
#define main unused_pilot_fixture
#include "v3_villager_text_test.c"
#undef main
#include "../overlays/v3/clothing.c"
#include "../overlays/v3/villager_readers.c"

struct Clothing af_v3_clothing;
int af_v3_clothing_dma(void *destination, unsigned int source, unsigned int count) {
    (void)destination; (void)source; (void)count;
    assert(0 && "Text/default lookup must not transfer clothing");
    return -1;
}
int af_v3_reader_name(u8 *out, u32 size, u32 npc) { return af_v3_load_name(out, size, npc); }

int main(void) {
    u8 raw[640], alias_data[AF_NPC_ALIAS_BYTES], words[AF_NPC_WORD_BYTES] = {0};
    u8 out[32], before[sizeof(animal)], field_bytes[50];
    assert(fread(raw, 1, sizeof(raw), stdin) == sizeof(raw));
    assert(fread(alias_data, 1, sizeof(alias_data), stdin) == sizeof(alias_data));
    assert(getchar() == EOF);
    AfNpcMailSources sources = {.words=words, .aliases=alias_data, .ready=0x41464353};
    actor[2] = 3;
    af_v3_clothing = (struct Clothing){.item=0x34BF, .index=0x10BF,
        .vrom=AF_V3_CLOTHING_VROM, .enabled=1};
    memcpy(af_v3_land_info, "Forest!!\x12\x34", 10);
    for (u32 i=0; i<20; ++i) {
        const u8 *data=raw+32*i;
        struct Villager *row=af_v3_villagers+i;
        memcpy(row, data, 32);
        row->actor=(u32)data[0]*256+data[1];
        row->cloth=(u32)data[2]*256+data[3];
        row->native_cloth=(u32)data[30]*256+data[31];
        assert(row->actor==0xE0DA+i && row->present==1);
    }
    for (u32 i=0; i<20; ++i) {
        struct Villager *row=af_v3_villagers+i;
        memset(out, 0xA5, sizeof(out));
        assert(af_v3_load_name(out+1, 8, row->actor)==1);
        assert(!memcmp(out+1, raw+32*i+8, 8) && out[0]==0xA5 && out[9]==0xA5);
        af_v3_short_name(out+1, row->actor&255);
        assert(!memcmp(out+1, raw+32*i+8, 6) && out[0]==0xA5 && out[9]==0xA5);
        assert(af_v3_get_looks(row->actor)==raw[32*i+4]);
        memset(animal, 0xA5, sizeof(animal));
        animal[0]=row->actor>>8; animal[1]=row->actor;
        memcpy(before, animal, sizeof(before));
        memcpy(before+0x4E5, row->key, 4);
        af_v3_reset_phrase(actor);
        assert(!memcmp(before, animal, sizeof(before)));
        memset(out, 0xA5, sizeof(out));
        assert(af_v3_load_phrase(out+1, 10, row->actor, animal+0x4E5)==1);
        assert(!memcmp(out+1, raw+32*i+16, 10) && out[0]==0xA5 && out[11]==0xA5);
        assert(af_v3_load_phrase(out+1, 10, 0xE000, row->key)==1);
        assert(!memcmp(out+1, row->phrase, 10));
        assert(af_v3_load_phrase(out+1, 10, af_v3_villagers[(i+1)%20].actor, row->key)==1);
        assert(!memcmp(out+1, row->phrase, 10));
        memset(field_bytes, 0xA5, sizeof(field_bytes));
        AfMailField *field=(AfMailField *)(field_bytes+16);
        assert(af_v3_mail_source_name(field, &sources, row->actor)==1);
        assert(field->length==8 && !memcmp(field->text, row->name, 8));
        assert(af_v3_mail_source_alias(field, &sources, row->name)==1);
        assert(field->length==8 && !memcmp(field->text, row->name, 8));
        for (u32 j=0; j<16; ++j) assert(field_bytes[j]==0xA5 && field_bytes[34+j]==0xA5);
        memset(animal, 0xA5, sizeof(animal));
        memcpy(before, animal, sizeof(before));
        af_v3_set_index(animal, row->actor&255);
        if (row->native_cloth) {
            before[0]=row->actor>>8; before[1]=row->actor; before[11]=row->personality;
            memcpy(before+2, "\x12\x34" "Forest", 8);
            memcpy(before+0x4E5, row->key, 4);
            before[0x520]=row->native_cloth>>8; before[0x521]=row->native_cloth;
        }
        assert(!memcmp(before, animal, sizeof(before)));
    }
    struct Villager *disabled=af_v3_villagers+9;
    disabled->present=0;
    memset(field_bytes, 0xA5, sizeof(field_bytes));
    assert(!af_v3_mail_source_alias((AfMailField *)(field_bytes+16), &sources, disabled->name));
    for (u32 j=0; j<sizeof(field_bytes); ++j) assert(field_bytes[j]==0xA5);
    puts("All twenty actual names, full phrases, saved aliases, dependencies, and guards pass");
    return 0;
}
