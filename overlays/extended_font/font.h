#ifndef AF_EXTENDED_FONT_H
#define AF_EXTENDED_FONT_H

#define AF_GLYPH_COUNT 5u
#define AF_GLYPH_BYTES 1600u
#define AF_GLYPH_TEXTURE_OFFSET 64u

/* Optional resource ownership belongs to the caller; no saved bytes are changed. */
int af_glyph_bind(const unsigned char *resource, unsigned int bytes);
int af_glyph_index(const unsigned char *text, unsigned int bytes);
unsigned int af_glyph_size(const unsigned char *text, unsigned int bytes);
unsigned int af_glyph_width(const unsigned char *text, unsigned int bytes);
int af_glyph_string_width(const unsigned char *text, unsigned int bytes);
unsigned int af_glyph_begin(const unsigned char *text, unsigned int bytes);
void af_glyph_end(unsigned int previous);
int af_glyph_code_width(unsigned int code, int cut);
int af_glyph_texture_code(int code);
const unsigned char *af_glyph_texture(void);

#endif
