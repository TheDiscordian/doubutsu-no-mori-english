#ifndef AF_V3_NPC_IDENTITY_H
#define AF_V3_NPC_IDENTITY_H
/* One donor-derived row for every additional special character. Sound spec
 * controls speech cadence; it is not the model's full voice programme. */
typedef struct {
    unsigned short name,sex;
    unsigned int sound;
    unsigned char text[8];
} AFNpcIdentity;
typedef struct {
    unsigned int magic,version,count,stride;
    AFNpcIdentity rows[8];
} AFNpcIdentities;
extern const AFNpcIdentities af_npc_identities;
int af_npc_identity_name(unsigned char *,unsigned int,unsigned int);
void af_npc_identity_actor_name(unsigned char *,const unsigned char *);
int af_npc_identity_sex(unsigned int);
int af_npc_identity_sound(unsigned int);
int af_npc_previous_name(unsigned char *,unsigned int,unsigned int);
void af_npc_previous_actor_name(unsigned char *,const unsigned char *);
int af_npc_previous_sex(unsigned int);
int af_npc_previous_sound(unsigned int);
#endif
