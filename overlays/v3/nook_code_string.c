#include "nook_code_string.h"
int af_np_code_string(unsigned char *text,int *length,int index,const unsigned char *code) {
    unsigned char row[28];
    int i,n=0,growth;
    if(!text || !length || !code || *length<2 || *length>1024 ||
       index<0 || index>*length-2 || text[index]!=0x7F ||
       (text[index+1]!=0x34 && text[index+1]!=0x35))return 0;
    for(i=0;i<14;i++) {
        unsigned char c=code[i];
        if(c=='#') {row[n++]=0x80;row[n++]=0xD1;}
        else if((c>='A' && c<='Z') || (c>='a' && c<='z') ||
                (c>='0' && c<='9') || c=='%' || c=='&' || c=='@')row[n++]=c;
        else return 0;
    }
    growth=n-2;
    if(*length>1024-growth)return -1;
    for(i=*length-1;i>=index+2;i--)text[i+growth]=text[i];
    for(i=0;i<n;i++)text[index+i]=row[i];
    *length+=growth;
    return 1;
}
