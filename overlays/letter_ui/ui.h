#ifndef AF_LETTER_UI_H
#define AF_LETTER_UI_H
extern int af_ui_load_name(unsigned char *, unsigned int, unsigned int);
extern int af_ui_width(unsigned int, int);
extern void af_ui_draw(void *, const unsigned char *, int, float, float,
                       int, int, int, int, int, int, float, float, int);
unsigned int af_ui_address_name(unsigned char *, const unsigned char *);
const unsigned char *af_ui_prompt(const unsigned char *, int *);
void af_ui_defaults(unsigned char *, unsigned int);
#endif
