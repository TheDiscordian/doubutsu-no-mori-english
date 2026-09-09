#include <string.h>
unsigned int af_quest_reply_calls,af_quest_reply_errors,af_quest_reply_item;
unsigned int af_quest_reply_log[4];
unsigned char af_quest_reply_fields[200],af_quest_reply_animal[12];
static void event(unsigned int value) {
    if (af_quest_reply_calls<4u) af_quest_reply_log[af_quest_reply_calls]=value;
    ++af_quest_reply_calls;
}
void af_quest_reply_test_name(unsigned char *out,const unsigned char *id) {
    event(1u);memcpy(af_quest_reply_animal,id,12);memcpy(out,"NATIVE",6);
}
void af_quest_reply_test_item(unsigned char *out,unsigned int id) {
    event(3u);af_quest_reply_item=id;memcpy(out,"OLD ITEM  ",10);
}
void af_quest_reply_test_field(unsigned int slot,const unsigned char *text,unsigned int size) {
    event(slot==6u?2u:4u);
    if (!((slot==6u && size==6u)||(slot==0u && size==10u))) { ++af_quest_reply_errors;return; }
    memcpy(af_quest_reply_fields+slot*10u,text,size);
    memset(af_quest_reply_fields+slot*10u+size,' ',10u-size);
}
