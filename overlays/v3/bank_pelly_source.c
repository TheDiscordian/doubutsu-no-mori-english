/* Included after complete extracted Pelly conversation functions. The caller
 * owns native actor publication and maps source actions explicitly. */
static int af_pg_busy;
static void af_pg_setup(NPC_POSTGIRL_ACTOR *p,GAME_PLAY *g,int action) {
    (void)g;p->action=action;
}
int af_bank_pelly_step(AFBankPelly *state,int operation) {
    if(af_pg_busy || !state || state->draw_type<0 || state->draw_type>1 ||
        state->status<0 || state->status>7 || state->action<0 || state->action>29 ||
        state->next_action<0 || state->next_action>29 || state->balance>999999999u ||
        state->loan>999999999u || (state->submenu_open!=0 && state->submenu_open!=1) ||
        (state->has_bank_account!=0 && state->has_bank_account!=1))return 0;
    if(operation<AF_BANK_PELLY_STATUS || operation>AF_BANK_PELLY_TALK)return 0;
    if((operation==AF_BANK_PELLY_MOVE || operation==AF_BANK_PELLY_INIT) &&
        (state->action<24 || state->action>28))return 0;
    af_pg_busy=1;
    AFBankPellyPrivate private={{state->loan},state->balance};af_pg_private=&private;
    NPC_POSTGIRL_ACTOR p={{{state->draw_type}},state->status,state->desk_full,state->has_bank_account,
        state->action,state->next_action,af_pg_setup,
        (unsigned short)(state->draw_type?SP_NPC_POST_GIRL2:SP_NPC_POST_GIRL)};
    GAME_PLAY game={{state->submenu_open}};
    if(operation==AF_BANK_PELLY_STATUS)aPG_set_post_status(&p);
    else if(operation==AF_BANK_PELLY_TALK)aPG_set_talk_info(&p);
    else if(operation==AF_BANK_PELLY_BUSINESS)aPG_ask_for_business(&p,&game);
    else if(operation==AF_BANK_PELLY_CONTINUE)aPG_repay_after_init(&p,&game);
    else if(operation==AF_BANK_PELLY_INIT) {
        if(p.action==25)aPG_msg_win_close_wait_init(&p,&game);
        else if(p.action==26)aPG_deposit_menu_close_wait_init(&p,&game);
        else if(p.action==27)aPG_deposit_after_recover_init(&p,&game);
        else if(p.action==28)aPG_repay_after_init(&p,&game);
    } else {
        if(p.action==24)aPG_deposit_before(&p,&game);
        else if(p.action==25)aPG_msg_win_close_wait(&p,&game);
        else if(p.action==26)aPG_deposit_menu_close_wait(&p,&game);
        else if(p.action==27)aPG_msg_win_open_wait(&p,&game);
        else if(p.action==28)aPG_deposit_after(&p,&game);
    }
    state->status=p.status;state->action=p.action;state->next_action=p.next_action;
    state->desk_full=p.is_desk_full;af_pg_private=0;af_pg_busy=0;return 1;
}
