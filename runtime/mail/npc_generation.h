#ifndef AF_NPC_MAIL_GENERATION_H
#define AF_NPC_MAIL_GENERATION_H

/* A synchronous, caller-owned session. Its event code and complete state must
 * remain allocated until native metadata creation and publication finish.
 * No pointer from this structure belongs in a saved letter.
 */
typedef struct AfNpcMailSession AfNpcMailSession;
struct AfNpcMailSession {
    int (*event)(AfNpcMailSession *, unsigned int, const void *, unsigned int);
    unsigned char *stage;
    const unsigned char *player;
    const unsigned char *animal;
    const unsigned char *remail;
    unsigned int condition;
    unsigned int foreign;
    unsigned int initial_capital;
};

typedef struct {
    const unsigned char *player;
    const unsigned char *animal;
    const unsigned char *remail;
} AfNpcMailPrepare;

enum {
    AF_NPC_PREPARE_BEGIN, AF_NPC_PREPARE_END, AF_NPC_SENDER_NAME,
    AF_NPC_OTHER_NAME, AF_NPC_WORD, AF_NPC_COMPOSITE, AF_NPC_CLASSIC,
    AF_NPC_INVALID_CALL
};

extern AfNpcMailSession *af_npc_mail_session;
void af_npc_mail_prepare(const unsigned char *, const unsigned char *, const unsigned char *);
void af_npc_mail_sender_name(unsigned char *, const unsigned char *);
void af_npc_mail_other_name(unsigned char *, const unsigned char *);
void af_npc_mail_word(unsigned char *, unsigned int, unsigned int);
int af_npc_mail_composite(unsigned char *, unsigned int, unsigned int, unsigned int, unsigned int, unsigned int);
void af_npc_mail_classic(unsigned char *, unsigned int *, unsigned char *, unsigned char *, unsigned int);

#endif
