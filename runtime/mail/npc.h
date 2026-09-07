#ifndef AF_MAIL_NPC_H
#define AF_MAIL_NPC_H

/* Scores belong to one complete, validated record for one synchronous send.
 * The body pointer identifies that record; it is never used to infer a header.
 */
typedef struct {
    const unsigned char *body;
    unsigned int ordinary, legacy;
    int nonspaces;
} AfMailNpcContext;

extern AfMailNpcContext *af_mail_npc_context;

int af_mail_send_npc(const unsigned char *mail);
unsigned int af_mail_grade_length(int *length, const unsigned char *body);

#endif
