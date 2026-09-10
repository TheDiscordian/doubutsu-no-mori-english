/* Check every new resident hook before installing font/world/mail together. */
#include "accent_mail.h"
typedef unsigned int u32;
extern int af_world_font_install(void);
struct MailHook { u32 address,first,second; const void *target; };
static const struct MailHook mail_hooks[] = {
    {0x80197654u,0x27BDFB38u,0xAFBF04C4u,af_accent_mail_format},
    {0x80196C28u,0x14800003u,0,af_accent_mail_restore},
    {0x80196B34u,0x1080003Au,0x00001025u,af_accent_catalog_header_valid},
    {0x801992A8u,0x14800003u,0x00001025u,af_accent_next_line}
};
#ifdef __mips__
static volatile u32 *word(u32 address) { return (volatile u32 *)address; }
static void flush(void) {
    ((void (*)(void *,u32))0x8002FE00u)((void *)0x80196B34u,0x277Cu);
    ((void (*)(void *,u32))0x80034CE0u)((void *)0x80196B34u,0x277Cu);
}
#else
extern volatile u32 *af_accent_test_word(u32);
extern void af_accent_test_flush(void);
#define word af_accent_test_word
#define flush af_accent_test_flush
#endif

int af_accent_font_install(void) {
    u32 i;
    for (i=0;i<sizeof(mail_hooks)/sizeof(mail_hooks[0]);++i) {
        volatile const u32 *native=word(mail_hooks[i].address);
        if (native[0]!=mail_hooks[i].first || native[1]!=mail_hooks[i].second) return 0;
    }
    if (!af_world_font_install()) return 0;
    for (i=0;i<sizeof(mail_hooks)/sizeof(mail_hooks[0]);++i) {
        volatile u32 *native=word(mail_hooks[i].address);
        native[0]=0x08000000u|(((u32)(unsigned long)mail_hooks[i].target&0x0FFFFFFFu)>>2);
        native[1]=0;
    }
    flush();
    return 1;
}
