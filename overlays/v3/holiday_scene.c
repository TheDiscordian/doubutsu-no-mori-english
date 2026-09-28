#include "holiday_scene.h"
#include "holiday_native.h"
extern const unsigned char af_holiday_scene_titles[208];
extern volatile short af_holiday_scene_event,af_holiday_scene_flags;
extern unsigned char *af_holiday_scene_demo;
extern int af_holiday_scene_original_init(void);
static unsigned int half(const unsigned char *p) {return (unsigned int)p[0]*256+p[1];}
static unsigned int word(const unsigned char *p) {return half(p)*65536u+half(p+2);}
int af_holiday_scene_message(const unsigned char *p,unsigned int bytes,unsigned int donor,unsigned int flags) {
    if(!p || bytes!=208 || word(p)!=0x41464854 || half(p+4)!=1 || half(p+6)!=128 ||
       word(p+8)!=32 || word(p+12)!=208)return -1;
    if(donor>=128 || p[16+donor]==255)return 0;
    unsigned int title=p[16+donor];if(title>=16)return -1;
    unsigned int message=half(p+144+2*(title+(flags==1?0:16)));
    return message && message<32768?(int)message:-1;
}
int af_holiday_scene_demo_init(void) {
    int result=af_holiday_scene_original_init(),type=af_holiday_scene_event;
    if(type<AF_HN_FIRST || type>=AF_HN_END)return result;
    unsigned int donor=af_holiday_source_ids[type];
    if(af_holiday_native_type(donor)!=type || !af_holiday_scene_demo)return 0;
    int message=af_holiday_scene_message(af_holiday_scene_titles,208,donor,(unsigned short)af_holiday_scene_flags);
    if(message<0)return 0;
    /* The actual native emsg message field is a 32-bit word at +300. */
    *(unsigned int *)(af_holiday_scene_demo+0x300)=(unsigned int)message;
    return result;
}
