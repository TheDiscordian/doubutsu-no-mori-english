#ifndef AF_V3_BANK_PELLY_H
#define AF_V3_BANK_PELLY_H
/* Borrowed source fields, not the N64 actor or saved layout. */
typedef struct {
    int draw_type,status,action,next_action,desk_full;
    unsigned int loan,balance;
    int submenu_open,has_bank_account;
} AFBankPelly;
enum {AF_BANK_PELLY_STATUS,AF_BANK_PELLY_BUSINESS,AF_BANK_PELLY_MOVE,
      AF_BANK_PELLY_INIT,AF_BANK_PELLY_CONTINUE,AF_BANK_PELLY_TALK};
/* Source action numbers remain source action numbers at this boundary. */
int af_bank_pelly_step(AFBankPelly *,int);
/* Return zero only for an unowned path, so original repayment may continue. */
int af_bank_pelly_native_business(void *,void *);
int af_bank_pelly_native_talk(void *);
void af_bank_pelly_native_move(void *,void *);
int af_bank_pelly_native_release(void *);
int af_bank_native_eligible(void);
int af_bank_native_selected(void);
extern unsigned char af_bank_account_mode;
extern unsigned char af_bank_home_arrangement;
extern unsigned char af_bank_native_homes[];
/* The completed source conversation is still linked through checked native
 * message/menu services by the future cartridge installer. */
#endif
