#include "diary.h"
typedef af_diary_u8 u8;
typedef af_diary_u32 u32;
typedef __UINTPTR_TYPE__ address;
static void copy(void *out,const void *in,u32 n) {
    u8 *d=out;const volatile u8 *s=in;while(n--)*d++=*s++;
}
static void fill(void *out,u8 value,u32 n) {volatile u8 *p=out;while(n--)*p++=value;}
static int equal(const u8 *a,const u8 *b,u32 n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static u8 *calendar(AFDiary *d,u32 player) {return d->bytes+AF_DIARY_HEADER+player*AF_DIARY_PLAYER;}
static const u8 *cal(const AFDiary *d,u32 player) {return d->bytes+AF_DIARY_HEADER+player*AF_DIARY_PLAYER;}
static u8 *page(AFDiary *d,u32 player,u32 month) {return calendar(d,player)+AF_DIARY_CALENDAR+month*AF_DIARY_PAGE;}
static u32 length(const u8 *p) {u32 n=AF_DIARY_PAGE;while(n && p[n-1]==32)n--;return n;}

void af_diary_reset(AFDiary *d) {
    if(!d)return;
    fill(d,0,sizeof(*d));copy(d->bytes,"AFDY\0\1",6);
    for(u32 p=0;p<AF_DIARY_PLAYERS;p++)fill(page(d,p,0),32,AF_DIARY_MONTHS*AF_DIARY_PAGE);
}
int af_diary_valid(const AFDiary *d) {
    if(!d || !equal(d->bytes,(const u8 *)"AFDY\0\1",6))return 0;
    for(u32 i=6;i<AF_DIARY_HEADER;i++)if(d->bytes[i])return 0;
    for(u32 p=0;p<AF_DIARY_PLAYERS;p++) {
        const u8 *c=cal(d,p);
        /* Bit 31 cannot represent a day. Reserved calendar bytes stay zero. */
        for(u32 m=0;m<24;m++)if(c[m*4]&128)return 0;
        if(c[96] || (c[97]&128) || c[98]>1 || c[99] || c[102]>12 || c[103])return 0;
        if(!(c[100]|c[101]) && c[102])return 0;
    }
    return 1;
}
int af_diary_player_clear(AFDiary *d,u32 p) {
    if(p>=AF_DIARY_PLAYERS || !af_diary_valid(d))return AF_DIARY_ARGUMENT;
    fill(calendar(d,p),0,AF_DIARY_CALENDAR);fill(page(d,p,0),32,AF_DIARY_MONTHS*AF_DIARY_PAGE);
    return AF_DIARY_OK;
}
int af_diary_lock(AFDiary *d,u32 viewer,u32 owner,int locked) {
    if(viewer>=AF_DIARY_PLAYERS || owner>=AF_DIARY_PLAYERS || (locked!=0 && locked!=1) ||
       !af_diary_valid(d))return AF_DIARY_ARGUMENT;
    if(viewer!=owner)return AF_DIARY_READONLY;
    calendar(d,owner)[98]=(u8)locked;return AF_DIARY_OK;
}
const u8 *af_diary_page(const AFDiary *d,u32 viewer,u32 owner,u32 month) {
    if(viewer>=AF_DIARY_PLAYERS || owner>=AF_DIARY_PLAYERS || month>=AF_DIARY_MONTHS ||
       !af_diary_valid(d) || (viewer!=owner && cal(d,owner)[98]))return 0;
    return cal(d,owner)+AF_DIARY_CALENDAR+month*AF_DIARY_PAGE;
}
int af_diary_layout(const u8 *text,u32 len,u32 cursor,const u8 *widths,AFDiaryLayout *out) {
    AFDiaryLayout result;AFDiaryPoint at={0,0,0};
    if(!text || !widths || !out || len>AF_DIARY_PAGE || cursor>len)return AF_DIARY_ARGUMENT;
    fill(&result,0,sizeof(result));
    for(u32 i=0;i<len;i++) {
        u32 code=text[i],w=code==0xCD?0:widths[code];
        if(code!=0xCD && (code<32 || code==0x7F || code==0x80 || !w || w>12))return AF_DIARY_ARGUMENT;
        if(at.x+w>AF_DIARY_WIDTH) {
            if(at.row+1>=AF_DIARY_ROWS)return AF_DIARY_FULL;
            at.row++;at.column=at.x=0;result.lines[at.row].start=(unsigned short)i;
        }
        if(i==cursor)result.cursor=at;
        result.lines[at.row].length++;
        if(code==0xCD) {
            if(at.row+1>=AF_DIARY_ROWS)return AF_DIARY_FULL;
            at.row++;at.column=at.x=0;result.lines[at.row].start=(unsigned short)(i+1);
        } else {at.column++;at.x+=w;result.lines[at.row].width=at.x;}
    }
    if(!widths[32] || widths[32]>12)return AF_DIARY_ARGUMENT;
    if(at.row+1<AF_DIARY_ROWS && at.x+widths[32]>AF_DIARY_WIDTH) {
        at.row++;at.column=at.x=0;result.lines[at.row].start=(unsigned short)len;
    }
    if(cursor==len)result.cursor=at;
    result.end=at;result.rows=at.row+1;copy(out,&result,sizeof(result));return AF_DIARY_OK;
}
static int draft_valid(const AFDiaryDraft *d) {
    if(!d || d->length>AF_DIARY_PAGE || d->cursor>d->length || d->player>=4 ||
       d->month>=12 || d->readonly>1 || d->scroll>AF_DIARY_ROWS-AF_DIARY_VISIBLE)return 0;
    for(u32 i=d->length;i<AF_DIARY_PAGE;i++)if(d->text[i]!=32)return 0;
    return 1;
}
static void visible(AFDiaryDraft *d,const AFDiaryLayout *layout) {
    u32 max=layout->rows>AF_DIARY_VISIBLE?layout->rows-AF_DIARY_VISIBLE:0;
    if(d->scroll>max)d->scroll=max;
    if(layout->cursor.row<d->scroll)d->scroll=layout->cursor.row;
    if(layout->cursor.row>=d->scroll+AF_DIARY_VISIBLE)d->scroll=layout->cursor.row-AF_DIARY_VISIBLE+1;
}
int af_diary_begin(AFDiaryDraft *d,const AFDiary *data,u32 viewer,u32 owner,u32 month,const u8 *widths) {
    AFDiaryDraft result;AFDiaryLayout layout;
    if(!d || !data || !widths || !separate(d,sizeof(*d),data,sizeof(*data)))return AF_DIARY_ARGUMENT;
    const u8 *p=af_diary_page(data,viewer,owner,month);
    if(!p)return viewer<4 && owner<4 && month<12 && af_diary_valid(data)?AF_DIARY_LOCKED:AF_DIARY_ARGUMENT;
    fill(&result,0,sizeof(result));copy(result.text,p,AF_DIARY_PAGE);copy(result.original,p,AF_DIARY_PAGE);
    result.length=result.cursor=length(p);result.player=owner;result.month=month;result.readonly=viewer!=owner;
    int status=af_diary_layout(result.text,result.length,result.cursor,widths,&layout);
    if(status!=AF_DIARY_OK)return status;
    /* Reading opens at the top; the editor reveals the end cursor on input. */
    copy(d,&result,sizeof(result));return AF_DIARY_OK;
}
int af_diary_command(AFDiaryDraft *d,u32 command,int code,const u8 *widths) {
    AFDiaryDraft result;AFDiaryLayout layout;int status;
    if(!draft_valid(d) || !widths || command<1 || command>8 || command==5)return AF_DIARY_ARGUMENT;
    if(d->readonly)return AF_DIARY_READONLY;
    copy(&result,d,sizeof(result));
    status=af_diary_layout(d->text,d->length,d->cursor,widths,&layout);
    if(status!=AF_DIARY_OK)return status;
    if(command==1) {if(!result.cursor)return 0;result.cursor--;}
    else if(command==4 && result.cursor<result.length)result.cursor++;
    else if(command==6) {
        if(!result.cursor)return 0;
        result.cursor--;result.length--;
        for(u32 i=result.cursor;i<result.length;i++)result.text[i]=result.text[i+1];
        result.text[result.length]=32;
    } else if(command==2 || command==3) {
        int target=(int)layout.cursor.row+(command==2?1:-1),best=-1,distance=193,x=0;
        if(target<0)return 0;
        if(target>layout.end.row) {
            if(command==3 || result.cursor!=result.length)return 0;
            command=8;code=0xCD;
        } else {
            AFDiaryLine *line=&layout.lines[target];
            for(u32 i=line->start;i<line->start+line->length ||
                (i==result.length && target==layout.end.row);i++) {
                int delta=x-layout.cursor.x;if(delta<0)delta=-delta;
                if(delta<=distance) {best=(int)i;distance=delta;}
                if(i==result.length)break;
                if(result.text[i]!=0xCD)x+=widths[result.text[i]];
            }
            if(best<0)return 0;
            result.cursor=(unsigned short)best;
        }
    }
    if(command==4 && d->cursor==d->length) {command=8;code=32;}
    if(command==7 || command==8) {
        if(command==7 && (!result.cursor || code==-1))return 0;
        if(code<32 || code>255 || code==0x7F || code==0x80)return AF_DIARY_ARGUMENT;
        if(command==7)result.text[result.cursor-1]=(u8)code;
        else {
            if(result.length==AF_DIARY_PAGE)return AF_DIARY_FULL;
            for(u32 i=result.length;i>result.cursor;i--)result.text[i]=result.text[i-1];
            result.text[result.cursor++]=(u8)code;result.length++;
        }
    }
    status=af_diary_layout(result.text,result.length,result.cursor,widths,&layout);
    if(status!=AF_DIARY_OK)return status;
    visible(&result,&layout);copy(d,&result,sizeof(result));return AF_DIARY_OK;
}
int af_diary_scroll(AFDiaryDraft *d,int delta,const u8 *widths) {
    AFDiaryLayout layout;
    if(!draft_valid(d) || !widths || delta < -AF_DIARY_ROWS || delta>AF_DIARY_ROWS)return AF_DIARY_ARGUMENT;
    int status=af_diary_layout(d->text,d->length,d->cursor,widths,&layout);
    if(status!=AF_DIARY_OK)return status;
    int next=(int)d->scroll+delta,max=layout.rows>AF_DIARY_VISIBLE?layout.rows-AF_DIARY_VISIBLE:0;
    if(next<0)next=0;
    if(next>max)next=max;
    if(next==d->scroll)return 0;
    d->scroll=(unsigned short)next;return AF_DIARY_OK;
}
int af_diary_commit(AFDiary *live,AFDiaryDraft *d,AFDiary *scratch,const u8 *widths,
                    AFDiaryCapacity capacity,void *ctx) {
    AFDiaryLayout layout;
    if(!draft_valid(d) || !af_diary_valid(live) || !scratch || !capacity || !widths ||
       !separate(live,sizeof(*live),scratch,sizeof(*scratch)) ||
       !separate(live,sizeof(*live),d,sizeof(*d)) || !separate(scratch,sizeof(*scratch),d,sizeof(*d)))
        return AF_DIARY_ARGUMENT;
    if(d->readonly)return AF_DIARY_READONLY;
    u8 *p=page(live,d->player,d->month);
    if(!equal(p,d->original,AF_DIARY_PAGE))return AF_DIARY_CHANGED;
    int status=af_diary_layout(d->text,d->length,d->cursor,widths,&layout);
    if(status!=AF_DIARY_OK)return status;
    copy(scratch,live,sizeof(*live));copy(page(scratch,d->player,d->month),d->text,AF_DIARY_PAGE);
    if(capacity(ctx,scratch)<0)return AF_DIARY_CAPACITY;
    copy(p,d->text,AF_DIARY_PAGE);copy(d->original,d->text,AF_DIARY_PAGE);return AF_DIARY_OK;
}
