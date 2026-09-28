/* Fixed carried identities, shared by every diary consumer. */
#ifndef AF_DIARY_ITEMS_H
#define AF_DIARY_ITEMS_H
#define AF_DIARY_ITEM_FIRST 0x2B10u
#define AF_DIARY_ITEM_COUNT 16u
#define AF_DIARY_COVER_FIRST 0x30FCu
#define AF_DIARY_ITEM_CATEGORY 44u
typedef unsigned char DiaryByte;
typedef unsigned short DiaryHalf;
typedef unsigned int DiaryWord;
typedef struct {
    DiaryHalf item, cover, price;
    DiaryByte category, style, name[16];
} AFDiaryItem;
_Static_assert(sizeof(AFDiaryItem)==24,"Diary item stride");
int af_diary_item_name(DiaryByte *,DiaryWord,DiaryWord);
int af_diary_item_type(DiaryWord);
DiaryWord af_diary_item_price(DiaryWord);
DiaryHalf af_diary_item_display(DiaryWord),af_diary_item_pocket(DiaryWord);
DiaryWord af_diary_item_collection(DiaryWord),af_diary_item_icon(DiaryWord);
#endif
