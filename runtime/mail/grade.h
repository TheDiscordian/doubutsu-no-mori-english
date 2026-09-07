#ifndef AF_MAIL_GRADE_H
#define AF_MAIL_GRADE_H

#define AF_MAIL_GRADE_MAX 1024u
#define AF_MAIL_CHECK_BYTES 5808u
#define AF_MAIL_CHECK_RELOC_BYTES 592u
#define AF_MAIL_CHECK_MAGIC 0x41464D47u

typedef struct {
    int components[7];
    int total;
    unsigned int rank;
} AfMailGrade;

/* Body bytes are ordinary text, never a snapshot. Short native bodies are
 * virtually space-padded to the English reference's 192-byte capacity.
 * Larger complete bodies retain their supplied capacity, up to 1024 bytes.
 * Output must not overlap the supplied body. Failure leaves output unchanged;
 * no input byte is modified when the buffers satisfy this requirement.
 */
int af_mail_grade(AfMailGrade *output, const unsigned char *body, unsigned int size);
int af_mail_word_rate(int *words, const unsigned char *body, unsigned int size);

/* Resident loader; invokes the separately installed on-demand scorer. */
int af_mail_grade_body(AfMailGrade *output, const unsigned char *body, unsigned int size);
int af_mail_word_rate_body(int *words, const unsigned char *body, unsigned int size);
unsigned int af_mail_grade_native(const unsigned char *body);

#endif
