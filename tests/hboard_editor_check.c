/* Sanitizer exercise with synthetic text, not extracted game assets. */
#include <assert.h>
#include <stddef.h>
#include <string.h>
#include "../runtime/hboard_editor.h"

int main(void) {
    unsigned char widths[256], native[64], english[92], saved[72];
    struct af_hboard_draft draft, old;
    struct af_hboard_layout layout;
    unsigned int random = 41928;
    int i, step, result;
    memset(widths, 6, sizeof(widths));
    memset(native, 0xA1, sizeof(native));
    memset(english, 'x', sizeof(english));
    english[18] = english[46] = english[69] = 0xCD;
    memset(saved, '!', sizeof(saved));
    memcpy(saved+4, native, sizeof(native));
    assert(af_hboard_begin(&draft, saved+4, native, english) == 1);
    assert(af_hboard_layout(draft.text, draft.length, 0, widths, &layout) == 1);
    assert(layout.rows == 4);
    assert(af_hboard_commit(&draft, native, english, saved+4) == 1);
    assert(memcmp(saved+4, native, 64) == 0);
    for (step = 0; step < 10000; ++step) {
        int command, code;
        random = random*1664525u+1013904223u;
        command = 1+(int)((random >> 9)%8);
        code = (random & 15u) == 0 ? 0xCD : (int)('a'+(random%26));
        old = draft;
        result = af_hboard_command(&draft, command, code, widths);
        if (result < 0) assert(memcmp(&draft, &old, sizeof(draft)) == 0);
        assert(draft.length <= 128 && draft.cursor <= draft.length);
        assert(af_hboard_layout(draft.text, draft.length, draft.cursor, widths, &layout) == 1);
        for (i = draft.length; i < 128; ++i) assert(draft.text[i] == ' ');
        assert(memcmp(saved+4, native, 64) == 0); /* Editing is not a saved write. */
    }
    assert(saved[0] == '!' && saved[3] == '!' && saved[68] == '!' && saved[71] == '!');
    assert(af_hboard_begin(NULL, saved+4, native, english) == -1);
    assert(af_hboard_begin(&draft, NULL, native, english) == -1);
    assert(af_hboard_layout(NULL, 0, 0, widths, &layout) == -1);
    assert(af_hboard_layout(draft.text, 129, 0, widths, &layout) == -1);
    assert(af_hboard_command(NULL, 8, 'x', widths) == -1);
    assert(af_hboard_pack(NULL, native, english, saved+4) == -1);
    assert(af_hboard_commit(NULL, native, english, saved+4) == -1);
    memset(draft.text, 'a', 128); draft.length = draft.cursor = 128;
    assert(af_hboard_layout(draft.text, 128, 128, widths, &layout) == 1);
    assert(af_hboard_command(&draft, 8, 'a', widths) == -4);
    assert(af_hboard_pack(&draft, native, english, saved+4) == -5);
    assert(memcmp(saved+4, native, 64) == 0);
    return 0;
}
