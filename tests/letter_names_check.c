#include <assert.h>
#include <string.h>
#include <stdint.h>

extern void af_letter_header(void *, void *, void *, float, float, const unsigned char *);
extern void af_letter_cursor(void *, void *, float, float);
extern unsigned int af_letter_prefix_width(const unsigned char *, unsigned int);
static unsigned char board[192], editor[96], saved_board[192], saved_editor[96];
static unsigned int menu[24];
static unsigned char colour[3] = {11, 22, 33}, full[8];
static int available = 1, state_missing, loads, draws, native_cursor, point, cursor_calls;
static unsigned int last_id;
static float cx, cy;
static struct {unsigned char text[20], colour[3]; unsigned int length; float x,y;} span[3];
unsigned char *af_letter_test_state(void *sub, unsigned int at) {
    assert(sub == (void *)1);
    if (state_missing) return 0;
    assert(at == 0x106E4 || at == 0x106E0);
    return at == 0x106E4 ? board : editor;
}
int af_load_display_name(unsigned char *out, unsigned int capacity, unsigned int id) {
    assert(capacity == 8 && id >= 0xE000 && id <= 0xE0D7); last_id=id; ++loads;
    if (!available) return 0;
    memcpy(out,full,8); return 1;
}
int af_letter_code_width(unsigned int code, int flags) {
    assert(!flags); return code == 'i' || code == 'I' || code == '\'' ? 4 : code >= 0x80 ? 12 : 6;
}
void af_mail_draw(void *game, const unsigned char *text, unsigned int length,
                  float x, float y, const unsigned char *rgb) {
    assert(game == (void *)2 && draws < 3 && length <= 18);
    memcpy(span[draws].text,text,length); memcpy(span[draws].colour,rgb,3);
    span[draws].length=length; span[draws].x=x; span[draws].y=y; ++draws;
}
void af_mail_snapshot_header(void *sub, void *game, void *m, float x, float y, const unsigned char *rgb) {
    (void)sub; (void)game; (void)m; (void)x; (void)y; (void)rgb;
    assert(0 && "Editing must not consult a persistent snapshot from an earlier read");
}
void af_letter_native_cursor(void *sub, void *game, float x, float y) {
    assert(sub == (void *)1 && game == (void *)2); ++native_cursor; cx=x; cy=y;
}
void af_letter_native_point(void *sub, void *game, float x, float y) {
    assert(sub == (void *)1 && game == (void *)2); ++point; cx=x; cy=y;
}
void af_letter_test_cursor(void *sub, void *game, unsigned char *e, float x, float y) {
    assert(sub == (void *)1 && game == (void *)2 && e == editor); ++cursor_calls; cx=x; cy=y;
}
static void snapshot(void) {memcpy(saved_board,board,sizeof(board));memcpy(saved_editor,editor,sizeof(editor));}
static void unchanged(void) {assert(!memcmp(saved_board,board,sizeof(board)));assert(!memcmp(saved_editor,editor,sizeof(editor)));}
static void clear_counts(void) {loads=draws=native_cursor=point=cursor_calls=0;}
static void setup(void) {
    memset(board,0,sizeof(board));memset(editor,0,sizeof(editor));memset(menu,0,sizeof(menu));
    board[3]=6;board[5]=10;board[0x2F]=4;board[0x18]=1;board[0x14]=12;
    memcpy(board+8,"Native",6);memcpy(board+0x32,"Hi, !     ",10);menu[1]=1;
    available=1;state_missing=0;clear_counts();snapshot();
}
int main(void) {
    setup();memcpy(full,"Puddles ",8);
    af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
    assert(loads == 1 && last_id == 0xE00C && draws == 3 && span[1].length == 8);
    assert(!memcmp(span[1].text,full,8) && span[1].colour[0] == 185 && !span[1].colour[1] && !span[1].colour[2]);
    assert(span[0].length == 4 && span[0].x == 64 && span[1].x == 86 && span[2].x == 166);
    assert(span[2].length == 6 && !memcmp(span[2].text,"!     ",6));
    board[0]=1;snapshot();clear_counts();af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
    assert(span[1].length == 7);
    for (int kind=0;kind<5;++kind) {
        setup();
        if (kind == 0) available=0;
        if (kind == 1) board[0x18]=0;
        if (kind == 2) board[0x18]=7;
        if (kind == 3) board[0x14]=216;
        if (kind == 4) board[0x14]=255;
        snapshot();af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
        assert(loads == (kind == 0) && span[1].length == 6 && !memcmp(span[1].text,"Native",6));
    }
    /* Museum identity remains canonical in every editing/animation state. */
    for (unsigned int status=0;status<=4;++status) {
        for (unsigned int field=0;field<3;++field) {
            setup();menu[1]=status;board[0]=(unsigned char)field;board[0x18]=2;
            memcpy(board+8,"\x19\x07\xF8\x11\x05\xC3",6);snapshot();
            af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
            assert(!loads);
            if (status == 1) {
                assert(draws == 3 && span[1].length == 6);
                assert(!memcmp(span[1].text,"Museum",6));
                assert(span[1].colour[0] == 185 && span[2].x == 166);
            } else {
                assert(draws == 1 && span[0].length == 16);
                assert(!memcmp(span[0].text,"Hi, Museum!     ",16));
            }
        }
    }
    setup();board[0x14]=215;board[0x2F]=10;snapshot();
    af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();assert(draws == 2 && last_id == 0xE0D7);
    for (int status=0;status<=4;++status) {
        if (status == 1) continue;
        setup();menu[1]=(unsigned int)status;
        af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
        assert(loads == 1 && draws == 1 && span[0].length == 17);
        assert(!memcmp(span[0].text,"Hi, Puddles!     ",17));
        assert(span[0].x == 64 && span[0].y == 36 && !memcmp(span[0].colour,colour,3));
        memcpy(full,"Octavian",8);clear_counts();
        af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
        assert(draws == 1 && span[0].length == 18 && !memcmp(span[0].text,"Hi, Octavian!     ",18));
        memcpy(full,"Puddles ",8);
    }
    for (int kind=0;kind<6;++kind) {
        setup();menu[1]=0;board[0x30]=(unsigned char)kind;snapshot();
        af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
        if (kind == 2 || kind == 3 || kind == 5) {
            assert(!loads && draws == 1 && span[0].length == 10);
            assert(!memcmp(span[0].text,board+0x32,10));
        } else assert(loads == 1 && draws == 1 && span[0].length == 17);
    }
    setup();menu[1]=0;available=0;board[3]=4;snapshot();
    af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();
    assert(draws == 1 && span[0].length == 14 && !memcmp(span[0].text,"Hi, Nati!     ",14));
    for (int kind=0;kind<8;++kind) {
        setup();
        if (kind >= 4) menu[1]=0;
        if (kind%4 == 0) board[5]=11;
        if (kind%4 == 1) board[0x2F]=11;
        if (kind%4 == 2) board[3]=7;
        if (kind%4 == 3) state_missing=1;
        snapshot();af_letter_header((void *)1,(void *)2,menu,64,36,colour);unchanged();assert(!draws && !loads);
    }
    setup();*(short *)(editor+0x20)=5;snapshot();
    af_letter_cursor((void *)1,(void *)2,10,20);unchanged();assert(cursor_calls == 1 && cx == 89 && cy == 16);
    board[2]=2;snapshot();clear_counts();af_letter_cursor((void *)1,(void *)2,10,20);unchanged();assert(cursor_calls == 1 && cx == 169 && cy == 16);
    board[2]=1;snapshot();clear_counts();af_letter_cursor((void *)1,(void *)2,10,20);unchanged();assert(point == 1 && cx == -16 && cy == 20);
    for (int field=1;field<=2;++field) {
        board[0]=(unsigned char)field;snapshot();clear_counts();af_letter_cursor((void *)1,(void *)2,10,20);unchanged();
        assert(native_cursor == 1 && cx == 10 && cy == 20 && !cursor_calls && !point);
    }
    for (int column=-1;column<=12;column+=13) {
        setup();*(short *)(editor+0x20)=(short)column;snapshot();af_letter_cursor((void *)1,(void *)2,10,20);unchanged();assert(!cursor_calls);
    }
    assert(af_letter_prefix_width((const unsigned char *)"i'I",3) == 12);
    assert(af_letter_prefix_width(0,3) == 0 && af_letter_prefix_width(board,11) == 0);
    setup();af_letter_header(0,(void *)2,menu,64,36,colour);af_letter_cursor(0,(void *)2,10,20);unchanged();assert(!draws && !cursor_calls);
    return 0;
}
