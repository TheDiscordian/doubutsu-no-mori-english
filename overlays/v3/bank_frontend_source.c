/* Included after all sixteen complete donor functions and the numerical API. */
static struct {
    Submenu submenu;
    Submenu_Overlay_c overlay;
    AFBankTransaction transaction;
    const AFBankFrontendOps *ops;
    void *context;
    int active,fault,busy;
} af_bn_ui;
static int af_bank_frontend_ready(void) {return af_bn_ui.active && !af_bn_ui.fault;}
static int af_bn_frame(void) {
    AFBankFrame f;
    if(!af_bn_ui.ops->frame(af_bn_ui.context,&f) || f.status<0 || f.status>4 ||
        f.next<0 || f.next>4 || f.direction<0 || f.direction>5 ||
        !(f.x>=-640 && f.x<=640 && f.y>=-640 && f.y<=640) ||
        !(f.texture_x>=-65536 && f.texture_x<=65536 &&
          f.texture_y>=-65536 && f.texture_y<=65536)) {
        af_bn_ui.fault=1;
        af_bn_ui.overlay.menu_info[mSM_OVL_BANK].proc_status=2;
        return 0;
    }
    mSM_MenuInfo_c *m=&af_bn_ui.overlay.menu_info[mSM_OVL_BANK];
    m->proc_status=f.status;m->next_proc_status=f.next;m->move_drt=f.direction;
    m->position[0]=f.x;m->position[1]=f.y;
    af_bn_ui.overlay.menu_control.trigger=(int)f.trigger;
    af_bn_ui.overlay.menu_control.texture_pos[0]=f.texture_x;
    af_bn_ui.overlay.menu_control.texture_pos[1]=f.texture_y;
    return 1;
}
static void af_bn_transition(int action,int direction) {
    af_bn_ui.ops->transition(af_bn_ui.context,action,direction);
    (void)af_bn_frame();
}
static void af_bn_pre_move(Submenu *s) {(void)s;af_bn_transition(AF_BANK_UI_PREMOVE,0);}
static void af_bn_pre_draw(Submenu *s,GAME *g) {(void)s;(void)g;af_bn_transition(AF_BANK_UI_PREDRAW,0);}
static void af_bn_move(Submenu *s,mSM_MenuInfo_c *m) {(void)s;(void)m;af_bn_transition(AF_BANK_UI_MOVE,0);}
static void af_bn_end(Submenu *s,mSM_MenuInfo_c *m) {(void)s;(void)m;af_bn_transition(AF_BANK_UI_END,0);}
static void af_bn_close(mSM_MenuInfo_c *m,int direction) {
    m->closed=1;af_bn_transition(AF_BANK_UI_CLOSE,direction);
}
static void af_bn_character(void *g) {af_bn_ui.ops->character_matrix(af_bn_ui.context,g);}
static void af_bank_frontend_play(Submenu *s,mSM_MenuInfo_c *m) {
    (void)s;
    unsigned char before[AF_BANK_BYTES],after[AF_BANK_BYTES];
    AFBankWallet original,wallet;unsigned int player;int eligible;
    if(af_bn_ui.fault || !af_bn_ui.ops->read(af_bn_ui.context,before,&original,&player,&eligible))return;
    for(unsigned int i=0;i<AF_BANK_BYTES;i++)after[i]=before[i];
    wallet=original;AFBankTransaction previous=af_bn_ui.transaction;
    int result=af_bank_step(after,sizeof(after),player,eligible,&wallet,&af_bn_ui.transaction,
        (u32)af_bn_ui.overlay.menu_control.trigger);
    if(result==AF_BANK_CONFIRM && af_bn_ui.ops->commit(af_bn_ui.context,before,after,&original,&wallet,player)!=1) {
        af_bn_ui.transaction=previous;result=AF_BANK_ERROR;
    }
    if(result==AF_BANK_CONFIRM || result==AF_BANK_CANCEL)af_bn_close(m,mSM_MOVE_OUT_TOP);
    unsigned int sound=result==AF_BANK_ERROR?0x1003u:af_bn_ui.transaction.sound;
    if(sound)af_bn_ui.ops->sound(af_bn_ui.context,sound);
}
int af_bank_frontend_open(const AFBankFrontendOps *ops,void *context) {
    unsigned char record[AF_BANK_BYTES];AFBankWallet wallet;unsigned int player;int eligible;
    if(af_bn_ui.active || af_bn_ui.busy || !ops || !context || !ops->read || !ops->commit ||
        !ops->frame || !ops->activate || !ops->transition || !ops->character_matrix || !ops->sound)return 0;
    af_bn_ui.busy=1;
    if(!ops->read(context,record,&wallet,&player,&eligible) ||
        af_bank_begin(record,sizeof(record),player,eligible,&wallet,&af_bn_ui.transaction)!=1) {
        af_bn_ui.busy=0;return 0;
    }
    af_bn_ui.ops=ops;af_bn_ui.context=context;af_bn_ui.fault=0;
    Submenu_Overlay_c *o=&af_bn_ui.overlay;
    /* The numerical scope is opened only for actual donor construction. Move
     * calls use the guarded transaction API, rather than direct native writes. */
    if(!source_open(&af_bn_ui.transaction.menu,&wallet,af_bn_ui.transaction.balance,&af_bn_ui.submenu,o)) {
        af_bn_ui.busy=0;return 0;
    }
    o->move_chg_base_proc=af_bn_close;o->move_Move_proc=af_bn_move;o->move_End_proc=af_bn_end;
    o->set_char_matrix_proc=af_bn_character;
    mSM_MenuInfo_c *m=&o->menu_info[mSM_OVL_BANK];
    *m=(mSM_MenuInfo_c){0};m->pre_move_func=af_bn_pre_move;m->pre_draw_func=af_bn_pre_draw;
    mBN_bank_ovl_construct(&af_bn_ui.submenu);af_bank_source_view=0;
    AFBankFrame f={m->proc_status,m->next_proc_status,m->move_drt,0,0,0,0,0};
    if(ops->activate(context,af_bank_frontend_move,af_bank_frontend_draw,&f)!=1) {
        mBN_bank_ovl_destruct(&af_bn_ui.submenu);af_bn_ui.transaction.open=0;
        af_bn_ui.busy=0;return 0;
    }
    af_bn_ui.active=1;af_bn_ui.busy=0;return 1;
}
void af_bank_frontend_move(void) {
    if(!af_bn_ui.active || af_bn_ui.busy || af_bn_ui.fault)return;
    af_bn_ui.busy=1;
    if(af_bn_frame())af_bn_ui.overlay.menu_control.menu_move_func(&af_bn_ui.submenu);
    af_bn_ui.busy=0;
}
int af_bank_frontend_draw(void *game) {
    if(!af_bn_ui.active || af_bn_ui.busy || af_bn_ui.fault || !game || !((GAME *)game)->graph)return 0;
    GRAPH *g=((GAME *)game)->graph;uptr start=(uptr)g->head,end=(uptr)g->tail;
    /* Eleven comma-formatted account digits, eleven cash digits, the title,
     * seven change characters, and OK. Charge the retained font's conservative
     * 256-byte-per-glyph draw allowance as well as frame commands. */
    if((start&7) || (end&7) || end<start || end-start<44u*256u+16u*8u)return 0;
    af_bn_ui.busy=1;
    if(!af_bn_frame()) {af_bn_ui.busy=0;return 0;}
    af_bn_ui.overlay.menu_control.menu_draw_func(&af_bn_ui.submenu,(GAME *)game);
    af_bn_ui.busy=0;return !af_bn_ui.fault;
}
void af_bank_frontend_destruct(void) {
    if(!af_bn_ui.active || af_bn_ui.busy)return;
    mBN_bank_ovl_destruct(&af_bn_ui.submenu);
    af_bn_ui.transaction.open=0;af_bn_ui.active=0;af_bn_ui.ops=0;af_bn_ui.context=0;
}
int af_bank_frontend_active(void) {return af_bn_ui.active;}
