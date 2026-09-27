#ifndef AF_CREATURE_INSECT_PLAYER_H
#define AF_CREATURE_INSECT_PLAYER_H
#include "creature_insects.h"

void af_insect_player_axe(void *,GAME *,int,int);
void af_insect_player_rock(void *,GAME *,int,int);
void af_insect_player_dig(void *,GAME *,int,int);
int af_insect_player_tree(u32,int,int);
extern const u32 af_insect_tree_bee_query;
extern const u32 af_insect_mosquito_message;
void *af_insect_player_resolve(u32);
void af_insect_mosquito_setup(void *,GAME *);
void af_insect_mosquito_main(void *,GAME *);
void af_insect_mosquito_notice_setup(void *,GAME *);
void af_insect_mosquito_notice_main(void *,GAME *);
void af_insect_mosquito_settle(void *,GAME *);
#ifndef __mips__
void *af_test_insect_player_resolve(u32);
#endif
#endif
