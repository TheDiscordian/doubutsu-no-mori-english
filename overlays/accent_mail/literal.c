/* New pair capture is restricted to complete source-approved item names. */
#include "accent_mail.h"

int af_accent_item_literal(const unsigned char *text,unsigned int length) {
    static const unsigned char names[4][16]={
        "caf\x80\x7C shirt", {'P','o','k',0x80,0x7C,'m','o','n',' ','P','i','k','a','c','h','u'},
        "Caf\x80\x7C K.K.", "Se\x80\x87or K.K."
    };
    static const unsigned char sizes[4]={11,16,10,11};
    unsigned int i,j;
    if(!text || length>16u)return 0;
    while(length && text[length-1u]==' ')--length;
    for(i=0;i<4u;++i) {
        if(length!=sizes[i])continue;
        for(j=0;j<length && text[j]==names[i][j];++j){}
        if(j==length)return 1;
    }
    return 0;
}
