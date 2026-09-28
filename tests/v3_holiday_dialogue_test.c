#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_dialogue.h"
static AFHolidayDialogue data;
static AFDiary diary;
static unsigned char rewards[4096],item_fields[5][16],free_fields[2][4];
static unsigned reward_size,calls,starts,orders,gives,marks,claimed_event,full;
static int last_message,last_continue;
static unsigned last_item,order_values[3];
static int item_name(unsigned char *p,unsigned cap,unsigned item) {
    if(!item || item==65535)return 0;
    assert(cap==16);memcpy(p,"complete English",16);last_item=item;return 1;
}
static const unsigned char *town(void) {return (const unsigned char *)"Leaf  ";}
static void set_item(void *w,int slot,const unsigned char *p,int n) {
    assert(w==&diary && slot>=0 && slot<5 && n==16);memcpy(item_fields[slot],p,16);calls++;
}
static void set_free(void *w,int slot,const unsigned char *p,int n) {
    assert(w==&diary && slot>=0 && slot<2 && n==4);memcpy(free_fields[slot],p,4);calls++;
}
static void turn(unsigned char n) {assert(n==1);calls++;}
static void camera(int n) {assert(n==3);calls++;}
static void message(int n) {last_message=n;calls++;}
static void continuation(void *w,int n) {assert(w==&diary);last_continue=n;calls++;}
static void listen(void) {calls++;}
static void start(void *a) {assert(a==&data);starts++;calls++;}
static void order(int kind,int index,unsigned short value) {
    assert(kind==5 && index>=0 && index<3);order_values[index]=value;orders++;calls++;
}
static AFHolidayTransport transport={&data,&diary,item_name,town,set_item,set_free,
    turn,camera,message,continuation,listen,start,order};
static unsigned be32(const unsigned char *p) {return (unsigned)p[0]<<24|(unsigned)p[1]<<16|(unsigned)p[2]<<8|p[3];}
static unsigned load(const char *path,unsigned char *out,unsigned capacity) {
    FILE *f=fopen(path,"rb");assert(f);unsigned n=fread(out,1,capacity,f);assert(feof(f));fclose(f);return n;
}
static unsigned resolve(void *c,unsigned src) {(void)c;return src;}
static int claimed(void *c,unsigned event) {(void)c;return event==claimed_event;}
static int give(void *c,unsigned item) {(void)c;assert(item);gives++;return 1;}
static void mark(void *c,unsigned event) {(void)c;claimed_event=event;marks++;}
static int free_slots(void *c) {(void)c;return full?0:15;}
static int after(void *c) {(void)c;return 0;}
static void quest(void *c) {(void)c;}
static void send(AFHolidayAction *a) {assert(af_holiday_transport(&data,&transport,a));}
int main(int argc,char **argv) {
    assert(argc==3);unsigned char raw[1024];unsigned size=load(argv[1],raw,sizeof(raw));
    assert(size==640 && sizeof(data)==636);
    data.magic=be32(raw);data.version=be32(raw+4);data.count=be32(raw+8);
    for(unsigned i=0;i<3;i++) {
        data.ranges[i].first=be32(raw+12+12*i);data.ranges[i].end=be32(raw+16+12*i);
        data.ranges[i].target=be32(raw+20+12*i);
    }
    memcpy(data.days,raw+48,31*4);memcpy(data.events,raw+172,29*16);
    reward_size=load(argv[2],rewards,sizeof(rewards));
    unsigned target=12033,count=0;
    for(unsigned group=0;group<3;group++)for(unsigned n=data.ranges[group].first;n<data.ranges[group].end;n++) {
        assert(af_holiday_message(&data,n)==(int)target);
        AFHolidayAction a={.effects=AF_HOLIDAY_MESSAGE,.message=n};send(&a);
        assert(last_message==(int)target++);count++;
    }
    assert(count==347 && af_holiday_message(&data,0x339B)==-1);
    for(unsigned event=0;event<28;event++)for(full=0;full<2;full++) {
        af_diary_reset(&diary);claimed_event=99;gives=marks=orders=0;
        AFHolidayWorld w={.diary=&diary,.dates={23,9,29},.today={2007,1,1},.player=0,
            .free_slots=free_slots,.lighthouse_after=after,.lighthouse_start=quest,
            .rewards=rewards,.reward_bytes=reward_size,.items={0,resolve,claimed,give,mark}};
        AFHolidayTalk t={0};AFHolidayAction a;
        assert(af_holiday_talk_prepare(&t,&w,event,w.today,0,0,0,&a)==1);send(&a);
        assert(af_holiday_talk_start(&t,&w,&a)==1);send(&a);
        assert(af_holiday_talk_step(&t,&w,1,0,0,&a)==1);send(&a);
        assert(last_continue==af_holiday_message(&data,(event==27?0x3391:0x3280+10*event)+(full?2:3)));
        assert(!gives && !marks && !orders);
        assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==1);send(&a);
        assert(gives==!full && marks==!full && orders==(full?0:3));
        if(!full)assert(order_values[0]==last_item && order_values[1]==7 && order_values[2]==0);
        assert(af_holiday_talk_step(&t,&w,0,1,1,&a)==1);send(&a);
        assert(gives==!full && !t.active);
        /* Every event's visitor insertion uses full item/event fields. */
        w.player=4;assert(af_holiday_talk_prepare(&t,&w,event,w.today,0,0,0,&a)==1);send(&a);
        assert(af_holiday_talk_start(&t,&w,&a)==1);send(&a);
        assert(!memcmp(item_fields[0],"complete English",16));
        if(event==4)assert(!memcmp(item_fields[1],"Leaf Day        ",16));
        else assert(!memcmp(item_fields[1],data.events[event],16));
    }
    for(unsigned day=1;day<=31;day++) {
        AFHolidayAction a={.effects=AF_HOLIDAY_BEGIN|AF_HOLIDAY_LIGHTHOUSE_DATES,
            .lighthouse_dates={{2007,1,day},{2007,1,32-day}}};send(&a);
        assert(!memcmp(free_fields[0],data.days[day-1],4));
        assert(!memcmp(free_fields[1],data.days[31-day],4));
    }
    unsigned old=calls;AFHolidayAction bad={.effects=AF_HOLIDAY_MESSAGE,.message=65535};
    assert(!af_holiday_transport(&data,&transport,&bad) && calls==old);
    bad=(AFHolidayAction){.effects=AF_HOLIDAY_BEGIN|AF_HOLIDAY_ITEM_NAME,.item=65535};
    assert(!af_holiday_transport(&data,&transport,&bad) && calls==old);
    data.ranges[0].target=0xFFFFFFFF;assert(af_holiday_message(&data,0x3280)==-1);
    assert(!af_holiday_transport(&data,&transport,&bad) && calls==old);
    puts("holiday dialogue: 347 mappings, all 28 reward/visitor/full-pocket paths, dates, and guarded native-call transport pass");
}
