#ifndef AF_V3_BANK_FRONTEND_SOURCE_H
#define AF_V3_BANK_FRONTEND_SOURCE_H
#include "bank_frontend.h"
typedef float f32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct {u8 r,g,b,a;} rgba_t;
typedef struct {u32 a,b;} Gfx;
/* Only these reviewed native fields are read. The host fixture has its own
 * graphics object; its pointer width does not describe the N64 layout. */
typedef struct {
    u8 prefix[0x298];Gfx *head;void *tail;
} GRAPH;
struct AFBankSourceGame {GRAPH *graph;};
#ifdef __mips__
_Static_assert(__builtin_offsetof(GRAPH,head)==0x298,"Native opaque head");
_Static_assert(__builtin_offsetof(GRAPH,tail)==0x29C,"Native opaque tail");
#endif
typedef void (*mSM_MOVE_PROC)(Submenu *,mSM_MenuInfo_c *);
#ifndef AF_BANK_FRONTEND_TEST
static void af_bank_frontend_play(Submenu *,mSM_MenuInfo_c *);
static int af_bank_frontend_ready(void);
#endif
extern void af_bank_native_translate(float,float,float,int);
extern void af_bank_native_scale(float,float,float,int);
extern void *af_bank_native_matrix(void *);
extern float af_bank_native_width(const unsigned char *,int,int);
extern void af_bank_native_line(void *,const unsigned char *,int,float,float,
    int,int,int,int,int,int,float,float,int);
/* Font formatting runs the complete checked donor function. Width and glyph
 * emission bind the installed native English font, not the donor font ABI. */
#define Matrix_translate af_bank_native_translate
#define Matrix_scale af_bank_native_scale
#define _Matrix_to_Mtx_new af_bank_native_matrix
#define mFont_GetStringWidth af_bank_native_width
#define mFont_SetLineStrings af_bank_native_line
#define MTX_LOAD 0
#define MTX_MULT 1
#define G_MTX_NOPUSH 0
#define G_MTX_LOAD 2
#define G_MTX_MODELVIEW 0
#define mFont_MODE_POLY 0
#define OPEN_DISP(graph) {GRAPH *af_bn_graph=(graph);
#define CLOSE_DISP(graph) }
#define NOW_POLY_OPA_DISP (af_bn_graph->head)
#define SET_POLY_OPA_DISP(p) (af_bn_graph->head=(p))
static inline void af_bn_command(Gfx *p,u32 a,u32 b) {*p=(Gfx){a,b};}
#define gSPDisplayList(p,a) af_bn_command((p),0xDE000000u,(u32)(uptr)(a))
#define gSPMatrix(p,a,f) af_bn_command((p),0xDA380001u|(f),(u32)(uptr)(a))
#define AF_BN_RGBA(r,g,b,a) ((u32)(r)<<24|(u32)(g)<<16|(u32)(b)<<8|(u32)(a))
#define gDPSetPrimColor(p,m,l,r,g,b,a) af_bn_command((p),0xFA000000u|((m)<<8)|(l),AF_BN_RGBA(r,g,b,a))
#define gDPSetEnvColor(p,r,g,b,a) af_bn_command((p),0xFB000000u,AF_BN_RGBA(r,g,b,a))
/* Dolphin expresses width/height in pixels. Native RDP tile extents use four
 * units per pixel; retain the source origin and inclusive last pixel. */
#define gDPSetTileSize_Dolphin(p,t,s,u,w,h) af_bn_command((p),\
    0xF2000000u|(((u32)(s)&4095)<<12)|((u32)(u)&4095),\
    ((u32)(t)<<24)|(((u32)((s)+((w)-1)*4)&4095)<<12)|((u32)((u)+((h)-1)*4)&4095))
#ifndef AF_BANK_FRONTEND_TEST
static void none_proc1(Submenu *s,mSM_MenuInfo_c *m) {(void)s;(void)m;}
static void mem_clear(u8 *p,unsigned int n,int value) {while(n--)*p++=(u8)value;}
#endif
/* Values come from the generated whole font/name enum dependencies. */
#endif
