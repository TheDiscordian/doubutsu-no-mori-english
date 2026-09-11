#include <assert.h>
#include "feedback.h"

int main(void) {
    static const unsigned int buttons[9]={0xA00,0x800,0x900,0x200,0,0x100,0x600,0x400,0x500};
    static const unsigned int expected[9]={3,1,19,4,0,20,5,2,21};
    int row,col;
    for (row=0;row<3;++row) for (col=0;col<3;++col) {
        int i=row*3+col;
        assert(af_v2_stick(0,(col-1)*80,(1-row)*80)==expected[i]);
        assert(af_v2_stick(buttons[i],0,0)==expected[i]);
    }
    assert(af_v2_stick(0,24,-24)==0);
    assert(af_v2_stick(0,25,0)==20);
    assert(af_v2_stick(0,0,-25)==2);
    assert(af_v2_stick(0,-128,127)==3);
    assert(af_v2_stick(0,128,0)==0);
    assert(af_v2_stick(0,0,-129)==0);
    assert(af_v2_stick(0x300,80,80)==0);
    assert(af_v2_stick(0xC00,80,80)==0);
    assert(af_v2_stick(0x100,-80,80)==20); /* D-pad priority matches editor. */
    assert(af_v2_stick(0xF03F,0,0)==0); /* Face, shoulder, C: not stick movement. */
    /* Native 16.16 ortho element, font vertices in 1/16 px, 160 px viewport. */
    for (col=0;col<10;++col) {
        float x=67.5f+col*16.0f;
        float projected=160.0f+(af_v2_text_x(x)-160.0f)*16.0f*25.0f/65536.0f*160.0f;
        float error=projected-x;
        assert(error>-0.0001f && error<0.0001f);
    }
    assert(af_v2_text_scale(1.0f)*125.0f/128.0f==1.0f);
    return 0;
}
