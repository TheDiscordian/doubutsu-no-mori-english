#ifndef AF_NPC_MAIL_CAPTURE_H
#define AF_NPC_MAIL_CAPTURE_H

#include "generate.h"
#include "../../runtime/mail/npc_generation.h"

#define AF_NPC_WORD_BYTES 11328u
#define AF_NPC_ALIAS_BYTES 6368u

typedef struct {
    const unsigned char *words;
    const unsigned char *aliases;
    unsigned int ready;
} AfNpcMailSources;

typedef struct {
    AfNpcMailSession session;
    AfNpcMailSources sources;
    AfMailCapture capture;
    AfMailSelection selection;
    unsigned int phase;
    unsigned int failed;
    unsigned int words_seen;
    unsigned int names_seen;
} AfNpcMailCaptureWork;

/* Validate both complete hashes before publishing source pointers. Source
 * storage remains immutable and allocated throughout the capture lifetime.
 * On failure the output descriptor is unchanged; callers must check returns.
 */
int af_npc_mail_sources_init(AfNpcMailSources *, const unsigned char *, unsigned int,
                             const unsigned char *, unsigned int);
int af_npc_mail_source_word(AfMailField *, const AfNpcMailSources *, unsigned int, unsigned int);
int af_npc_mail_source_name(AfMailField *, const AfNpcMailSources *, unsigned int);
int af_npc_mail_source_alias(AfMailField *, const AfNpcMailSources *, const unsigned char *);

/* Callback for the scoped resident adapters. Phase three and failed zero are
 * required before generation. No destination letter is written here.
 */
int af_npc_mail_capture_event(AfNpcMailSession *, unsigned int, const void *, unsigned int);

#endif
