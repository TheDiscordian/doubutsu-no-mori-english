#include <stddef.h>
#include <string.h>
#include "../overlays/mail_generation/npc_creator.h"

unsigned char af_npc_word_data[AF_NPC_WORD_BYTES],af_npc_alias_data[AF_NPC_ALIAS_BYTES];
unsigned int af_npc_creator_calls,af_npc_creator_clear_calls,af_npc_creator_fault;
unsigned int af_npc_creator_ids[5],af_npc_creator_nested_result;
unsigned char af_npc_creator_before[164],af_npc_creator_nested_destination[164];
unsigned int af_npc_creator_nested_capital;
AfNpcMailCreateWork *af_npc_creator_nested_work;

unsigned int af_npc_creator_size(void) { return sizeof(AfNpcMailCreateWork); }
unsigned int af_npc_creator_stage_offset(void) { return offsetof(AfNpcMailCreateWork,stage); }
unsigned int af_npc_creator_generation_offset(void) { return offsetof(AfNpcMailCreateWork,generation); }
unsigned int af_npc_creator_text_offset(void) { return offsetof(AfNpcMailCreateWork,generation.text); }

int af_npc_creator_small_control_overlap(void) {
    unsigned int capital __attribute__((aligned(16))) = 0;
    AfNpcMailSession *active __attribute__((aligned(16))) = 0;
    unsigned char destination[164];
    memset(destination,'!',sizeof(destination));
    if (af_npc_mail_create((AfNpcMailCreateWork *)&capital,destination,&active,&capital)) return 0;
    if (af_npc_mail_create((AfNpcMailCreateWork *)&active,destination,&active,&capital)) return 0;
    return !capital && !active && destination[0] == '!' && destination[163] == '!';
}

void af_npc_creator_test_clear(unsigned char *stage) {
    ++af_npc_creator_clear_calls;
    /* Deliberately leave native structure padding alone; ownership must zero
     * the whole private record before this initializer runs.
     */
    memset(stage,0,17);memset(stage+18,0,17);memset(stage+36,0,6);
    stage[38] = 255;memset(stage+42,' ',122);
}

void af_npc_creator_test_metadata(unsigned char *stage, const unsigned char *player,
                                 const unsigned char *animal, const unsigned char *remail,
                                 unsigned int condition, unsigned int foreign) {
    unsigned int split;
    unsigned char header[10],footer[16];
    ++af_npc_creator_calls;
    memcpy(af_npc_creator_before,stage,164);
    if (af_npc_creator_fault == 1) return; /* Missing entire preparation. */
    if (af_npc_creator_fault == 2) {
        af_npc_creator_nested_result = af_npc_mail_create(af_npc_creator_nested_work,
            af_npc_creator_nested_destination,&af_npc_mail_session,&af_npc_creator_nested_capital);
    }
    af_npc_mail_prepare(player,animal,remail);
    if (af_npc_creator_fault == 3) return; /* Missing selected templates. */
    if (condition)
        af_npc_mail_composite(stage,af_npc_creator_ids[0],af_npc_creator_ids[1],af_npc_creator_ids[2],
                             af_npc_creator_ids[3],af_npc_creator_ids[4]);
    else
        af_npc_mail_classic(header,&split,footer,stage+0x34,af_npc_creator_ids[0]);
    memcpy(stage,player,16);stage[16] = 0;
    memcpy(stage+18,remail ? remail+4 : (const unsigned char *)"SENDER",6);
    memcpy(stage+24,remail ? remail+10 : (const unsigned char *)"TOWN  ",6);
    stage[30] = 0x12;stage[31] = 0x34;stage[32] = 0xE0;stage[33] = 0;stage[34] = 1;
    stage[36] = condition ? 0x10 : 0;stage[37] = condition ? 1 : 0;
    stage[38] = 0;stage[40] = 0;stage[41] = (unsigned char)(foreign+7);
    if (af_npc_creator_fault == 4) af_npc_mail_session = 0; /* Lost scope ownership. */
}
