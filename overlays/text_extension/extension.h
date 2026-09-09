#ifndef AF_TEXT_EXTENSION_H
#define AF_TEXT_EXTENSION_H
typedef unsigned int af_u32;
int af_text_extension_init(void);
void af_free_set(void *window, int slot, const unsigned char *source, int length);
int af_free_copy(void *window, int slot, unsigned char *data, int index, int length);
int af_free_colour(void *window, int *index, int slot, int colour);
void af_free_item(unsigned int item, int slot);
void af_free_item_nonzero(unsigned int item, int slot);
void af_free_item_colour(unsigned int item, int slot, int colour);
#endif
