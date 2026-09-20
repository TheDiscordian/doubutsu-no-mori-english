/* Shared source tool effects. Keep native foreground, hole, and buried-item
 * handling; apply the donor's shovel bonus only to its ordinary DIG result. */
typedef unsigned short u16;
typedef struct { float x, y, z; } DigPosition;
#ifdef __mips__
#define previous (*(volatile DigPosition *)0x804B2FD0u)
#define native_status ((int (*)(u16 *, DigPosition))0x8008CAD8u)
#define random_float ((float (*)(void))0x8002C9ACu)
#else
extern volatile DigPosition af_test_dig_previous;
extern int af_test_dig_status(u16 *, DigPosition);
extern float af_test_dig_random(void);
#define previous af_test_dig_previous
#define native_status af_test_dig_status
#define random_float af_test_dig_random
#endif

int af_v3_shovel_status(u16 *item, DigPosition position, int golden) {
    int status = native_status(item, position);
    if (status == 3) {
        if (golden == 1 &&
            (position.x > previous.x + 20.0f || position.x < previous.x - 20.0f ||
             position.z > previous.z + 20.0f || position.z < previous.z - 20.0f) &&
            (int)(random_float() * 10.0f) == 1) {
            status = 5;
            *item = 0x2103; /* ITM_MONEY_100 in both games. */
        }
        /* Ordinary digs count too, even when no bonus roll was made. */
        previous = position;
    }
    return status;
}
