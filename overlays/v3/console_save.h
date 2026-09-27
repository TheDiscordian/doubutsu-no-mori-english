#ifndef AF_V3_CONSOLE_SAVE_H
#define AF_V3_CONSOLE_SAVE_H

/* Shared AFNE recipe executor. No device I/O or resident storage is implied.
 * Keep four independent player blocks; the surrounding save codec owns their
 * checksums. Packet/context/buffers must remain alive and disjoint until close.
 * The loader authenticates the immutable packet before calling open. */
enum {
    AF_CONSOLE_PLAYERS = 4,
    AF_CONSOLE_PLAYER_BYTES = 0x660,
    AF_CONSOLE_SAVE_BYTES = AF_CONSOLE_PLAYERS * AF_CONSOLE_PLAYER_BYTES,
    AF_CONSOLE_PAYLOAD_BYTES = 1623,
    AF_CONSOLE_WORK_BYTES = 2048,
    AF_CONSOLE_BATTERY_BYTES = 8192,
    AF_CONSOLE_MAX_OPS = 64,
    AF_CONSOLE_BAD_ARGUMENT = -1,
    AF_CONSOLE_BAD_PACKET = -2,
    AF_CONSOLE_BAD_GAME = -3,
    AF_CONSOLE_BAD_STATE = -4
};
typedef struct {
    const unsigned char *packet, *operations;
    unsigned char *save, *work, *battery, *image;
    unsigned int operation_count, image_bytes, active;
    unsigned char score_state[AF_CONSOLE_MAX_OPS];
} AFConsoleSave;

/* Validates the full nineteen-game packet and all disjoint recipe ranges. */
int af_v3_console_validate(const unsigned char *packet, unsigned int bytes);
/* Loads the complete game image and applies first-play/returning-player data.
 * On failure neither the context nor any supplied buffer changes. The save
 * contains all four players, and player is an index 0..3. Header bytes 0..3
 * and byte 0x65F of each player remain owned by the surrounding codec. */
int af_v3_console_open(AFConsoleSave *state,
    const unsigned char *packet, unsigned int packet_bytes,
    unsigned int game, unsigned int player,
    unsigned char *save, unsigned int save_bytes,
    unsigned char *work, unsigned int work_bytes,
    unsigned char *battery, unsigned int battery_bytes,
    unsigned char *image, unsigned int image_bytes);
/* A frame waits for each game's default score before inserting its saved score.
 * Reset preserves flags only where the source recipe requests it. */
int af_v3_console_frame(AFConsoleSave *state, int reset);
/* Captures all battery/disk ranges, then invalidates the transient session. */
int af_v3_console_close(AFConsoleSave *state);
#endif
