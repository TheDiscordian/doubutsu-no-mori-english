#ifndef AF_V3_BANK_FRONTEND_H
#define AF_V3_BANK_FRONTEND_H
#include "bank_account.h"
typedef struct {
    int status,next,direction;
    unsigned int trigger;
    float x,y,texture_x,texture_y;
} AFBankFrame;
enum {AF_BANK_UI_PREMOVE,AF_BANK_UI_MOVE,AF_BANK_UI_END,
      AF_BANK_UI_PREDRAW,AF_BANK_UI_CLOSE};
/* A native owner supplies checked menu callbacks and complete snapshots. Commit
 * must reject a changed snapshot before any native write, then publish every
 * pocket/wallet/account change without a failure point. No donor struct is cast
 * to a native menu, Private, or saved-town record. */
typedef struct {
    int (*read)(void *,unsigned char [AF_BANK_BYTES],AFBankWallet *,unsigned int *,int *);
    int (*commit)(void *,const unsigned char *,const unsigned char *,
                  const AFBankWallet *,const AFBankWallet *,unsigned int);
    int (*frame)(void *,AFBankFrame *);
    int (*activate)(void *,void (*)(void),int (*)(void *),const AFBankFrame *);
    void (*transition)(void *,int,int);
    void (*character_matrix)(void *,void *);
    void (*sound)(void *,unsigned int);
} AFBankFrontendOps;
/* One transient submenu owner. It never owns persistent account storage. */
int af_bank_frontend_open(const AFBankFrontendOps *,void *);
void af_bank_frontend_move(void);
int af_bank_frontend_draw(void *game);
void af_bank_frontend_destruct(void);
int af_bank_frontend_active(void);
#endif
