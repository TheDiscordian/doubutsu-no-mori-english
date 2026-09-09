#ifndef AF_NOTICE_TREASURE_H
#define AF_NOTICE_TREASURE_H

#include "initial.h"

/* Native treasure profile: 01F0..0201, full sender/item text, numeric N64
 * row/column clues, and the native town identity without its Japanese suffix.
 * 01F4 retains its town/row-only clue; it never reveals the buried item.
 * These helpers do not select, bury, publish, or persist a treasure.
 */
unsigned int af_notice_treasure_mask(unsigned int);
int af_notice_treasure_valid(const AfMailRecord *);
int af_notice_treasure_pack(unsigned char *, unsigned int, const AfMailRecord *);

/* Decode into disposable aligned workspace. Its complete letter body is valid
 * only on success. Input and workspace must be disjoint; scratch can change on
 * failure. The normal saved record remains unchanged.
 */
int af_notice_treasure_decode(AfNoticeWorkspace *, const unsigned char *, unsigned int);

/* Equivalent caller-owned scratch split into existing mail-creator members.
 * The three scratch ranges and saved input must be pairwise disjoint. This
 * avoids a second allocation or incompatible-structure casts in the creator.
 */
int af_notice_treasure_decode_parts(AfMailWorkspace *, AfMailText *, unsigned char *,
                                     const unsigned char *, unsigned int);

/* Publish a complete body, clearing unused output bytes. Failure preserves the
 * entire output. Output may overlap the saved input, but not workspace.
 */
int af_notice_treasure_restore(AfNoticeText *, const unsigned char *, unsigned int,
                                AfNoticeWorkspace *);

#endif
