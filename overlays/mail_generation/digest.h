#ifndef AF_MAIL_SOURCE_DIGEST_H
#define AF_MAIL_SOURCE_DIGEST_H

/* Resource integrity only; all message/word/name provenance is checked by the
 * build tools against supplied sources. Input/output must not overlap.
 */
int af_mail_source_digest(unsigned char output[32], const unsigned char *input, unsigned int size);

#endif
