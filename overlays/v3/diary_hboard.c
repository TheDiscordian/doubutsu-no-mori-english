/* Appended to the existing HBOARD overlay. Its original functions retain their
 * relocations and remain the fallback for ordinary house-message editing. */
extern int af_diary_screen_init(void *),af_diary_screen_set_proc(void *);
extern void af_diary_screen_destruct(void *);
extern void af_diary_hboard_previous_init(void *),af_diary_hboard_previous_proc(void *);
extern void af_diary_hboard_previous_destruct(void *);
void af_diary_hboard_init(void *sub) {
    if(!af_diary_screen_init(sub))af_diary_hboard_previous_init(sub);
}
void af_diary_hboard_proc(void *sub) {
    if(!af_diary_screen_set_proc(sub))af_diary_hboard_previous_proc(sub);
}
void af_diary_hboard_destruct(void *sub) {
    af_diary_screen_destruct(sub);af_diary_hboard_previous_destruct(sub);
}
