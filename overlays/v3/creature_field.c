/* Complete imported frame objects; ordinary native banks keep their loader. */
typedef unsigned char u8;
typedef unsigned int u32;
extern int af_field_pi(u32,void *,u32);
extern int af_field_dma(void *,u32,u32,const char *,int);
extern u32 af_field_crc(const void *,u32);
extern void af_field_fault(const char *,const char *);
extern void af_field_scale(float,float,float,int);
extern void af_field_rotate_x(short,int),af_field_rotate_y(short,int),af_field_rotate_z(short,int);
#ifdef __mips__
#define metadata ((const u8 *)0x80648000u)
#else
extern const u8 *af_test_field_metadata;
#define metadata af_test_field_metadata
#endif

static u32 word(const u8 *p) {
    return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];
}

int af_v3_creature_graphics_load(void *destination,u32 vrom,u32 bytes,
                                const char *file,int line) {
    u32 i;
    /* These spans are the unchanged original banks, including their shadows. */
    if ((vrom>=0x1871000u && vrom<0x187FFA0u && bytes<=0x187FFA0u-vrom) ||
        (vrom>=0x113D000u && vrom<0x1146950u && bytes<=0x1146950u-vrom))
        return af_field_dma(destination,vrom,bytes,file,line);
    if (destination && !((__UINTPTR_TYPE__)destination&7) &&
        word(metadata)==0x41464346u && word(metadata+4)==1 && word(metadata+8)==17 && word(metadata+12)==24) {
        for(i=0;i<17;i++) {
            const u8 *row=metadata+16+i*24;
            u32 offset=word(row+8);
            if (word(row)==vrom && word(row+4)==bytes && bytes && !(bytes&15) &&
                bytes<=word(row+16) && offset<=AF_FIELD_POOL_BYTES &&
                bytes<=AF_FIELD_POOL_BYTES-offset) {
                if (!af_field_pi(AF_FIELD_POOL_ROM+offset,destination,bytes) &&
                    af_field_crc(destination,bytes)==word(row+12)) return 0;
                break;
            }
        }
    }
    af_field_fault("Creature graphics", "Invalid resource or transfer");
    return -1;
}

void af_v3_creature_insect_transform(const void *actor,int frame) {
    const u8 *p=actor;
    int species=*(const int *)(p+0x1CC),held=*(const int *)(p+0x1B8)==1;
    short x=*(const short *)(p+0xDC),y=*(const short *)(p+0xDE),z=*(const short *)(p+0xE0);
    const float *scale=(const float *)(p+0x5C);
    if(species<32) {
        /* Preserve the native scale/rotation order and all original held poses. */
        if(held) {
            x=y=0;
            if(species==13 || species==14 || species==16)y=-0x4000;
            else if(species!=27) {x=0x2000;y=(short)0x8000;}
        }
        af_field_scale(scale[0],scale[1],scale[2],1);
        af_field_rotate_x(x,1);af_field_rotate_y(y,1);
        return;
    }
    /* Added species use the actual donor pose and rotation order. The caller
       retains native translation, matrix transfer, alpha, and segment setup. */
    if(held) {
        x=0x4000;y=species==37 ? 0 : (short)0x8000;
        af_field_rotate_x(x,1);af_field_rotate_y(y,1);
    } else {
        if(species==33)af_field_rotate_y(y,1);
        af_field_rotate_x(x,1);
        if(species!=33 && !(species==37 && frame==2))af_field_rotate_y(y,1);
        af_field_rotate_z(z,1);
    }
    af_field_scale(scale[0],scale[1],scale[2],1);
}
