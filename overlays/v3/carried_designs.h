#ifndef AF_V3_CARRIED_DESIGNS_H
#define AF_V3_CARRIED_DESIGNS_H

/* Shared custom patterns, not copies embedded in each placed sign. The donor's
 * four players each own eight physical slots. Menu ordering is independent:
 * rearranging icons must not change the picture on an already placed object.
 * Names/palette/flags retain the source 0x220 record; pixels are native CI4.
 * This owned allocation is NOT padding in the native Private structure. */
enum { AF_DESIGN_PLAYERS=4, AF_DESIGN_SLOTS=8, AF_DESIGN_SIDE=32,
    AF_DESIGN_TEXELS=1024, AF_DESIGN_TEXTURE=512, AF_DESIGN_NAME=16,
    AF_DESIGN_PALETTES=16, AF_DESIGN_RECORD=544,
    AF_DESIGN_BYTES=4*8*544+4*8,
    AF_DESIGN_OK=1, AF_DESIGN_UNCHANGED=0, AF_DESIGN_ARGUMENT=-1,
    AF_DESIGN_CHANGED=-2, AF_DESIGN_CAPACITY=-3 };
typedef struct {
    unsigned char name[16],palette,flags,reserved[14],texture[512];
} __attribute__((aligned(32))) AFDesign;
typedef struct {
    AFDesign patterns[AF_DESIGN_PLAYERS][AF_DESIGN_SLOTS];
    unsigned char order[AF_DESIGN_PLAYERS][AF_DESIGN_SLOTS];
} AFDesigns;
typedef struct {
    AFDesign original,edited;
    unsigned int player,index;
} AFDesignDraft;
typedef struct { unsigned short queue[AF_DESIGN_TEXELS]; } AFDesignFillWork;
typedef int (*AFDesignCapacity)(void *,const AFDesigns *);
_Static_assert(sizeof(AFDesign)==AF_DESIGN_RECORD,"Design record layout");
_Static_assert(__builtin_offsetof(AFDesign,texture)==32,"Aligned CI4 pixels");
_Static_assert(sizeof(AFDesigns)==AF_DESIGN_BYTES,"Complete design allocation");

int af_design_valid(const AFDesigns *);
int af_design_reset(AFDesigns *,const AFDesign templates[8]);
int af_design_reset_player(AFDesigns *,unsigned int,const AFDesign templates[8]);
/* Read-only rendering always uses the physical slot; selection uses order[]. */
const AFDesign *af_design_physical(const AFDesigns *,unsigned int,unsigned int);
const AFDesign *af_design_selected(const AFDesigns *,unsigned int,unsigned int);
int af_design_reorder(AFDesigns *,unsigned int,unsigned int,unsigned int);
int af_design_begin(AFDesignDraft *,const AFDesigns *,unsigned int,unsigned int);
int af_design_pixel(const AFDesign *,int,int);
int af_design_paint(AFDesign *,int,int,unsigned int);
int af_design_fill(AFDesign *,int,int,unsigned int,AFDesignFillWork *);
int af_design_palette(AFDesign *,unsigned int);
int af_design_name(AFDesign *,const unsigned char *,unsigned int);
/* Preserve live state on cancel, stale edits, invalid input, or lack of save
 * space. Capacity measures the COMPLETE town, not just these compressible
 * patterns. The future native caller supplies disjoint menu-heap scratch and
 * flushes edited texture cache lines before publishing them to the RSP. */
int af_design_commit(AFDesigns *,const AFDesignDraft *,AFDesigns *,AFDesignCapacity,void *);
#endif
