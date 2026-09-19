/* Host bindings use the actual stock module and mock only native game APIs. */
extern Category af_test_event_categories[3];
extern u8 *af_test_event_owner;
extern int af_test_event_selected(u32);
extern u8 *af_test_event_get_area(u32,u32);
extern int af_v3_event_stock_init(Stock *);
extern int af_v3_event_stock_count(const Stock *,u32);
extern int af_v3_event_stock_index(const Stock *,u32,u32);
extern int af_v3_event_stock_quote(const Stock *,u32,Offer *);
extern int af_v3_event_stock_commit(Stock *,const Offer *);
static void *private_data;
static int get_order(u32,u32),choice_index(void *),free_count(void *,u32);
static int give_item(void *,u32,u32),name(u8 *,u32,u32),money_check(u32);
static void set_order(u32,u32,u32),continue_msg(void *,u32),demo_msg(u32),camera(u32);
static void *choice_window(void),*msg_window(void);
static void set_choices(void *,const u8 *,int,const u8 *,int,const u8 *,int,const u8 *,int);
static void native_info(Vendor *),payment(u32),price_string(u32,u32);
static Action native_action(u32);
#define categories af_test_event_categories
#define owner af_test_event_owner
#define selected af_test_event_selected
#define get_area(event,id) ((Stock *)af_test_event_get_area(event,id))
#define stock_init af_v3_event_stock_init
#define stock_count af_v3_event_stock_count
#define stock_index af_v3_event_stock_index
#define stock_quote af_v3_event_stock_quote
#define stock_commit af_v3_event_stock_commit
#define AF_V3_EVENT_NATIVE_FIRST 12007u
#define AF_V3_EVENT_ROUTE_MESSAGE 12010u
