#include "npc_generation.h"

AfNpcMailSession *af_npc_mail_session;

#ifdef __mips__
typedef char npc_session_size[sizeof(AfNpcMailSession) == 32 ? 1 : -1];
typedef char npc_prepare_size[sizeof(AfNpcMailPrepare) == 12 ? 1 : -1];
#define native_prepare ((void (*)(const unsigned char *,const unsigned char *,const unsigned char *))0x800A8C48u)
#define native_name ((void (*)(unsigned char *,const unsigned char *))0x800ACD18u)
#define native_word ((void (*)(unsigned char *,unsigned int,unsigned int))0x800C3F70u)
#define native_composite ((int (*)(unsigned char *,unsigned int,unsigned int,unsigned int,unsigned int,unsigned int))0x800A8B84u)
#define native_classic ((void (*)(unsigned char *,unsigned int *,unsigned char *,unsigned char *,unsigned int))0x80093F04u)
#else
extern void af_npc_test_prepare(const unsigned char *,const unsigned char *,const unsigned char *);
extern void af_npc_test_name(unsigned char *,const unsigned char *);
extern void af_npc_test_word(unsigned char *,unsigned int,unsigned int);
extern int af_npc_test_composite(unsigned char *,unsigned int,unsigned int,unsigned int,unsigned int,unsigned int);
extern void af_npc_test_classic(unsigned char *,unsigned int *,unsigned char *,unsigned char *,unsigned int);
#define native_prepare af_npc_test_prepare
#define native_name af_npc_test_name
#define native_word af_npc_test_word
#define native_composite af_npc_test_composite
#define native_classic af_npc_test_classic
#endif

static int event(AfNpcMailSession *session, unsigned int kind, const void *value, unsigned int count) {
    if (!session->event)
        return 0;
    return session->event(session,kind,value,count);
}

void af_npc_mail_prepare(const unsigned char *player, const unsigned char *animal, const unsigned char *remail) {
    AfNpcMailSession *session = af_npc_mail_session;
    AfNpcMailPrepare args;
    args.player = player; args.animal = animal; args.remail = remail;
    if (session)
        event(session,AF_NPC_PREPARE_BEGIN,&args,sizeof(args));
    /* Execute every original name, RNG, string load, and ten-byte setter. The
     * selected-ID/name hooks capture complete sources beside this preparation.
     */
    native_prepare(player,animal,remail);
    if (session)
        event(session,AF_NPC_PREPARE_END,&args,sizeof(args));
}

static void name(unsigned char *destination, const unsigned char *animal, unsigned int slot) {
    AfNpcMailSession *session = af_npc_mail_session;
    native_name(destination,animal);
    if (session)
        event(session,slot,animal,0);
}

void af_npc_mail_sender_name(unsigned char *destination, const unsigned char *animal) {
    name(destination,animal,AF_NPC_SENDER_NAME);
}

void af_npc_mail_other_name(unsigned char *destination, const unsigned char *animal) {
    name(destination,animal,AF_NPC_OTHER_NAME);
}

void af_npc_mail_word(unsigned char *destination, unsigned int capacity, unsigned int id) {
    AfNpcMailSession *session = af_npc_mail_session;
    native_word(destination,capacity,id);
    if (session)
        event(session,capacity == 10u ? AF_NPC_WORD : AF_NPC_INVALID_CALL,0,id);
}

int af_npc_mail_composite(unsigned char *mail, unsigned int header, unsigned int a,
                        unsigned int b, unsigned int c, unsigned int footer) {
    AfNpcMailSession *session = af_npc_mail_session;
    unsigned int selected[5];
    if (!session)
        return native_composite(mail,header,a,b,c,footer);
    if (mail != session->stage)
        return event(session,AF_NPC_INVALID_CALL,mail,0);
    selected[0] = header; selected[1] = a; selected[2] = b; selected[3] = c; selected[4] = footer;
    return event(session,AF_NPC_COMPOSITE,selected,5);
}

void af_npc_mail_classic(unsigned char *header, unsigned int *split, unsigned char *footer,
                       unsigned char *body, unsigned int id) {
    AfNpcMailSession *session = af_npc_mail_session;
    if (!session) {
        native_classic(header,split,footer,body,id);
        return;
    }
    if (!split || !session->stage || body != session->stage+0x34)
        event(session,AF_NPC_INVALID_CALL,body,0);
    else {
        event(session,AF_NPC_CLASSIC,&id,1);
        /* Native bad-reply creation reads this stack output before the whole
         * validated snapshot replaces its temporary copied text fields.
         */
        *split = 0;
    }
}
