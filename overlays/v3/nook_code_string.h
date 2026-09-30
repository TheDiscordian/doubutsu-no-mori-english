#ifndef AF_V3_NOOK_CODE_STRING_H
#define AF_V3_NOOK_CODE_STRING_H
/* Replace one item-string command with a complete fourteen-character row.
 * The two-byte hash tag can expand the row to 28 bytes. No sixteen-byte item
 * field is enlarged or written beyond its native allocation. */
int af_np_code_string(unsigned char *,int *,int,const unsigned char *);
#endif
