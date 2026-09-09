#ifndef AF_NOTICE_RECORD_H
#define AF_NOTICE_RECORD_H

#include "../mail/record.h"

#define AF_NOTICE_RECORD_BYTES 96u
#define AF_NOTICE_PAYLOAD_BYTES 92u

/* Codec only: callers must establish native text/tag discrimination and source
 * approval before installation. No timestamp, saved stride, or mail tag changes.
 * The family test recognises unsupported versions so they can fail visibly.
 */
int af_notice_record_tagged(const unsigned char *input, unsigned int size);
int af_notice_record_pack(unsigned char *output, unsigned int capacity,
                           const AfMailRecord *record);
/* Restore the canonical 122-byte codec input, never into a native board slot.
 * Both operations stage their output, support overlap, and publish only on
 * success. Unused bytes are zero and covered by canonical validation.
 */
int af_notice_record_expand(unsigned char *output, unsigned int capacity,
                             const unsigned char *input, unsigned int size,
                             unsigned int expected_catalog);

#endif
