#ifndef AF_V3_BANK_ACCOUNT_H
#define AF_V3_BANK_ACCOUNT_H
/* A separately owned, endian-neutral account record. Native Private padding
 * is not storage. The enclosing saved-town transaction must own this record. */
typedef unsigned char af_bank_u8;
typedef unsigned short af_bank_u16;
typedef unsigned int af_bank_u32;
enum { AF_BANK_BYTES=48,AF_BANK_PLAYERS=4,AF_BANK_POCKETS=15,
       AF_BANK_MAX=999999999,AF_BANK_WALLET_MAX=99999,
       AF_BANK_ERROR=-1,AF_BANK_PREVIEW=0,AF_BANK_CONFIRM=1,AF_BANK_CANCEL=2 };
typedef struct {
    af_bank_u32 wallet;
    af_bank_u16 items[AF_BANK_POCKETS];
    af_bank_u8 conditions[AF_BANK_POCKETS];
} AFBankWallet;
/* The complete donor menu's numeric state; never cast a native overlay to it. */
typedef struct {
    int player_max_bell,player_bell,now_bell,bank_bell,cursol,bell;
} AFBankMenu;
typedef struct {
    AFBankMenu menu;
    AFBankWallet original;
    af_bank_u32 player,balance,received,open,sound;
} AFBankTransaction;
typedef struct {af_bank_u32 balance,received;} AFBankAccount;
typedef struct {
    void *context;
    int (*exists)(void *,af_bank_u32);
    af_bank_u32 (*resolve)(void *,af_bank_u32);
    int (*submit)(void *,af_bank_u32,af_bank_u32,af_bank_u32,af_bank_u32);
} AFBankMailOps;
int af_bank_valid(const af_bank_u8 *,af_bank_u32);
int af_bank_reset(af_bank_u8 *,af_bank_u32);
int af_bank_clear(af_bank_u8 *,af_bank_u32,af_bank_u32);
int af_bank_get(const af_bank_u8 *,af_bank_u32,af_bank_u32,AFBankAccount *);
int af_bank_required(const af_bank_u8 *,af_bank_u32);
int af_bank_profile(const af_bank_u8 *,af_bank_u32,af_bank_u32);
int af_bank_bind(af_bank_u8 *,af_bank_u32,af_bank_u32);
int af_bank_eligible(af_bank_u32 resident,af_bank_u32 loan,af_bank_u32 house_size,af_bank_u32 renewing);
int af_bank_begin(const af_bank_u8 *,af_bank_u32,af_bank_u32,int,
    const AFBankWallet *,AFBankTransaction *);
/* Controller bits are the donor's existing N64-compatible button values.
 * Preview/cancel never write accounts or pockets. Confirmation validates the
 * original snapshot and conservation before publishing the whole transaction. */
int af_bank_step(af_bank_u8 *,af_bank_u32,af_bank_u32,int,
    AFBankWallet *,AFBankTransaction *,af_bank_u32);
/* The complete donor four-row, 64-byte resource, not an item allowlist.
 * Optional selection filters before the first eligible attempt. Receipt flags
 * change only when the real native mail submission returns exactly success. */
int af_bank_send_rewards(af_bank_u8 *,af_bank_u32,const af_bank_u8 *,af_bank_u32,
    const AFBankMailOps *);
/* Generated complete donor control/transfer functions, with a scoped borrowed
 * inventory view. Native UI, drawing, dialogue, money I/O, and saved ownership
 * still require explicit installed bindings. */
int af_bank_source_init(AFBankMenu *,const AFBankWallet *,af_bank_u32);
int af_bank_source_step(AFBankMenu *,AFBankWallet *,af_bank_u32 *,af_bank_u32,af_bank_u32 *);
#endif
