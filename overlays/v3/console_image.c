#include "console_image.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ address;
typedef struct {
    AFConsoleRead read;
    void *context;
    AFConsoleImageWork *work;
    u32 base,total,position,loaded,used,crc;
    int error;
} Reader;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static u32 crc_byte(u32 crc,u8 value) {
    crc^=value;
    for(u32 i=0;i<8;i++)crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1)));
    return crc;
}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static u8 next(Reader *r) {
    if(r->error)return 0;
    if(r->position==r->total) {r->error=AF_CONSOLE_BAD_PACKET;return 0;}
    if(r->used==r->loaded) {
        u32 remaining=r->total-r->position;
        r->loaded=remaining<AF_CONSOLE_INPUT_BYTES?remaining:AF_CONSOLE_INPUT_BYTES;
        if(r->read(r->context,r->base+r->position,r->work->data,(r->loaded+15)&~15u)) {
            r->error=AF_CONSOLE_READ_FAILED;return 0;
        }
        r->used=0;
    }
    u8 value=r->work->data[r->used++];
    r->position++;r->crc=crc_byte(r->crc,value);return value;
}
int af_v3_console_load_image(const u8 *metadata,u32 bytes,u32 game,
    AFConsoleRead read,void *context,u32 pool_bytes,u8 *image,u32 image_bytes,
    AFConsoleImageWork *workspace) {
    const u8 *entry,*descriptor;
    u32 packed,offset,out=0,image_crc=~0u;
    int result;
    if(!read || !image || !workspace || ((address)workspace&15) || !pool_bytes ||
        pool_bytes>0x4000000 || (pool_bytes&15) ||
        !separate(metadata,bytes,image,image_bytes) ||
        !separate(metadata,bytes,workspace,sizeof(*workspace)) ||
        !separate(image,image_bytes,workspace,sizeof(*workspace)))return AF_CONSOLE_BAD_ARGUMENT;
    if(!game || game>19)return AF_CONSOLE_BAD_GAME;
    result=af_v3_console_validate(metadata,bytes);
    if(result<0)return result;
    if(word(metadata+4)!=2)return AF_CONSOLE_BAD_PACKET;
    entry=metadata+32+(game-1)*64;descriptor=metadata+word(entry+16);
    packed=word(descriptor+24);offset=word(descriptor+20);
    if(image_bytes!=word(entry+20) || offset>pool_bytes ||
        ((packed+15)&~15u)>pool_bytes-offset)return AF_CONSOLE_BAD_ARGUMENT;
    Reader reader={read,context,workspace,offset,packed,0,0,0,~0u,0};
    u8 header[16];
    for(u32 i=0;i<16;i++)header[i]=next(&reader);
    if(reader.error)return reader.error;
    if(word(header)!=0x59617A30 || word(header+4)!=image_bytes || word(header+8) || word(header+12))
        return AF_CONSOLE_BAD_PACKET;
    while(out<image_bytes) {
        u32 flags=next(&reader);
        if(reader.error)return reader.error;
        for(u32 mask=128;mask && out<image_bytes;mask>>=1) {
            if(flags&mask) {
                u8 value=next(&reader);
                if(reader.error)return reader.error;
                image[out++]=value;image_crc=crc_byte(image_crc,value);
            } else {
                u32 first=next(&reader),second=next(&reader);
                u32 distance=((first&15)<<8)+second+1,length=first>>4;
                if(length)length+=2;else length=(u32)next(&reader)+18;
                if(reader.error)return reader.error;
                if(distance>out || length>image_bytes-out)return AF_CONSOLE_BAD_PACKET;
                while(length--) {
                    u8 value=image[out-distance];image[out++]=value;
                    image_crc=crc_byte(image_crc,value);
                }
            }
        }
    }
    /* Archive padding is authenticated, not interpreted as more game data. */
    while(reader.position<reader.total && !reader.error)(void)next(&reader);
    if(reader.error)return reader.error;
    if(~reader.crc!=word(descriptor+16) || ~image_crc!=word(entry+12))return AF_CONSOLE_BAD_PACKET;
    for(u32 i=0;i<16;i++)if(image[i]!=descriptor[i])return AF_CONSOLE_BAD_PACKET;
    return 0;
}
