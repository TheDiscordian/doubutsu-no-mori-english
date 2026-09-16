#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_FAN_SOUND 0x167
#define AF_V3_HELD_POINTER 0x804A3000u
#include "../overlays/v3/player_actions.c"

static u32 storage[0x12D8/4], backup[0x12D8/4];
static void *actor = storage, *game = (void *)0x1234;
static int kind, demo, trigger_a, held_a, allowed, requests, settled, bee;
static int walk_requests, wait_requests, polls, setup_calls, eye;
static int sound_calls, stopped;
static u32 model_pointer;
static int model_shape;
static s8 demo_controller[64];
static float move_x, move_y, frames[4];
static int init_args[4], events[32], event_count;
static void event(int value) { assert(event_count < 32); events[event_count++] = value; }

static void *get_player(void *g) { assert(g == game); return actor; }
static int get_kind(void *a, int action) {
    assert(a == actor && action == WORD(actor, 0xCF0)); return kind;
}
static int title_demo(void) { return demo; }
static const s8 *title_controller(void) { return demo_controller; }
static int trigger(int button) { assert(button == 0x8000); return trigger_a; }
static int held(int button) { assert(button == 0x8000); return held_a; }
static int check_request(void *g, int index, int priority) {
    assert(g == game && index == 109); event(1);
    return allowed && priority > WORD(actor, 0xD04);
}
static void request(void *g, int index, int priority) {
    assert(g == game && index == 109); event(2); ++requests;
    WORD(actor, 0xD00) = index; WORD(actor, 0xD04) = priority; WORD(actor, 0xD08) = 1;
}
static int umbrella(void *g, int priority) {
    assert(g == game && priority == 4); event(10); ++polls; return 0;
}
static void animation(void *a, void *g, int upper, int lower, float frame0,
                      float frame1, float speed, float morph, int mode, int part) {
    assert(a == actor && g == game); event(3);
    init_args[0] = upper; init_args[1] = lower; init_args[2] = mode; init_args[3] = part;
    frames[0] = frame0; frames[1] = frame1; frames[2] = speed; frames[3] = morph;
}
static void setup(void *a, void *g) {
    assert(a == actor && g == game); event(4); ++setup_calls;
    WORD(actor, 0xD04) = 4; WORD(actor, 0xD08) = WORD(actor, 0xD0C) = 0;
}
static void set_eye(void *a, int index) { assert(a == actor); event(5); eye = index; }
static int check_frame(void *fc, float frame) {
    assert(fc == (u8 *)actor + 0x174 && (frame == 7.5f || frame == 1.5f));
    float current = REAL(actor, 0x184), speed = REAL(actor, 0x180);
    return current - speed < frame && frame <= current;
}
static void settle(void *a) {
    assert(a == actor); event(6); ++settled;
    if (!WORD(actor, 0xD08) && !WORD(actor, 0xD0C) && WORD(actor, 0xD04) == 4) {
        WORD(actor, 0xD04) = 0; WORD(actor, 0xD0C) = 1;
    }
}
static void set_bee(void *a, int state) { assert(a == actor); event(7); bee = state; }
static float controller_x(void) { return move_x; }
static float controller_y(void) { return move_y; }
static int walk(void *g, void *position, float morph, int flags, int priority) {
    assert(g == game && !position && morph == -5.0f && flags == 0 && priority == 1);
    event(8); ++walk_requests;
    if (priority <= WORD(actor, 0xD04)) return 0;
    WORD(actor, 0xD00) = 8; WORD(actor, 0xD04) = priority; WORD(actor, 0xD08) = 1;
    return 1;
}
static int wait(void *g, float morph, int flags, int priority) {
    assert(g == game && morph == -5.0f && flags == 2 && priority == 1);
    event(9); ++wait_requests;
    if (priority <= WORD(actor, 0xD04)) return 0;
    WORD(actor, 0xD00) = 7; WORD(actor, 0xD04) = priority; WORD(actor, 0xD08) = 1;
    return 1;
}
static int brake(void *a) { assert(a == actor); event(11); return 1; }
static void reinput(void *a, void *g) { assert(a == actor && g == game); event(12); }
static int calculate(void *a, float *last) {
    assert(a == actor); event(13); *last = REAL(actor, 0x184);
    if (!stopped) {
        REAL(actor, 0x184) += REAL(actor, 0x180);
        if (REAL(actor, 0x184) >= REAL(actor, 0x178))
            REAL(actor, 0x184) += REAL(actor, 0x174) - REAL(actor, 0x178);
    }
    return stopped;
}
static int equal_frame(void *a, float last) {
    assert(a == actor); event(14); return REAL(actor, 0x184) == last;
}
static void sound(int id, void *position) {
    assert(id == AF_V3_FAN_SOUND && position == (u8 *)actor + 0x28); event(15); ++sound_calls;
}
static void recover(void *a) { assert(a == actor); event(16); }
static void correct(void *a, void *g) { assert(a == actor && g == game); event(17); }
static void background(void *a) { assert(a == actor); event(18); }
static void item(void *a, void *g) { assert(a == actor && g == game); event(19); }
static u32 model(int shape) { model_shape = shape; return model_pointer; }
void *af_test_player_function(u32 at) {
    switch (at) {
    case 0x800B1C84: return get_player;
    case 0x808BD5C4: return get_kind;
    case 0x8007D90C: return title_demo;
    case 0x800B593C: return title_controller;
    case 0x80078DAC: return trigger;
    case 0x80078D30: return held;
    case 0x808B8874: return check_request;
    case 0x808B3334: return request;
    case 0x808B7DD8: return umbrella;
    case 0x808B4A44: return animation;
    case 0x808B3BD0: return setup;
    case 0x808B36E8: return set_eye;
    case 0x808B5844: return check_frame;
    case 0x808B3648: return settle;
    case 0x808B3AF0: return set_bee;
    case 0x808B312C: return controller_x;
    case 0x808B3170: return controller_y;
    case 0x808C13F0: return walk;
    case 0x808C1064: return wait;
    case 0x808B3C74: return brake;
    case 0x808B61E4: return reinput;
    case 0x808B488C: return calculate;
    case 0x808B5698: return equal_frame;
    case 0x800D1D58: return sound;
    case 0x808B5310: return recover;
    case 0x808B4DAC: return correct;
    case 0x808B5FB0: return background;
    case 0x808BF410: return item;
    case AF_V3_HELD_POINTER: return model;
    default: assert(!"Unexpected native player API"); return NULL;
    }
}
static void reset(void) {
    memset(storage, 0, sizeof(storage)); memset(events, 0, sizeof(events)); event_count = 0;
    kind = 107; demo = trigger_a = held_a = 0; allowed = 1;
    requests = settled = bee = walk_requests = wait_requests = polls = setup_calls = eye = 0;
    sound_calls = stopped = 0;
    move_x = move_y = 0; WORD(actor, 0xCF0) = 109;
    REAL(actor, 0x174) = 1; REAL(actor, 0x178) = 9; REAL(actor, 0x180) = 1.0f;
}
int main(void) {
    reset(); trigger_a = 1;
    for (kind = -1; kind <= 115; ++kind) {
        assert(af_v3_player_fan_controller(game, 1) == (kind >= 107 && kind <= 114));
        assert(!af_v3_player_fan_controller(game, 0));
    }
    kind = 107; held_a = 1; trigger_a = 0;
    assert(!af_v3_player_fan_controller(game, 1) && af_v3_player_fan_controller(game, 0));
    demo = 1; demo_controller[0x38] = 1; demo_controller[0x39] = 0;
    assert(af_v3_player_fan_controller(game, 1) && !af_v3_player_fan_controller(game, 0));
    demo_controller[0x38] = 0; demo_controller[0x39] = 1;
    assert(!af_v3_player_fan_controller(game, 1) && af_v3_player_fan_controller(game, 0));

    reset(); allowed = 0; memset((u8 *)actor + 0xD58, 0xA5, 8);
    memcpy(backup, storage, sizeof(storage));
    assert(!af_v3_player_fan_request(game, 1, 4) && !requests);
    assert(!memcmp(storage, backup, sizeof(storage)));
    allowed = 1; assert(af_v3_player_fan_request(game, 1, 4));
    assert(WORD(actor, 0xD58) == 1 && WORD(actor, 0xD5C) == (int)0xA5A5A5A5);
    assert(WORD(actor, 0xD00) == 109 && WORD(actor, 0xD04) == 4 && WORD(actor, 0xD08) == 1);
    assert(!af_v3_player_fan_request(game, 0, 4) && requests == 1);

    for (int action = 7; action <= 11; ++action) {
        reset(); WORD(actor, 0xCF0) = action; trigger_a = 1;
        assert(af_v3_player_fan_check(game, 1, 1, 4) == (action == 7 || action == 11));
        WORD(actor, 0xD04) = 0; REAL(actor, 0x180) = 0.999f;
        assert(af_v3_player_fan_check(game, 1, 1, 4));
    }
    reset(); trigger_a = 1; af_v3_player_handheld_poll(game, 4);
    assert(polls == 1 && requests == 1 && events[0] == 10 && events[1] == 1 && events[2] == 2);

    reset(); WORD(actor, 0xD58) = 1; REAL(actor, 0x1F4) = 12.5f;
    af_v3_player_fan_setup(actor, game);
    assert(init_args[0] == 270 && init_args[1] == 0 && init_args[2] == 1 && init_args[3] == 4);
    assert(frames[0] == 1 && frames[1] == 1 && frames[2] == 1 && frames[3] == -5);
    assert(setup_calls == 1 && eye == 5 && events[0] == 3 && events[1] == 4 && events[2] == 5);
    WORD(actor, 0xD58) = 0; af_v3_player_fan_setup(actor, game);
    assert(frames[0] == 1 && frames[1] == 12.5f && frames[2] == 1 && frames[3] == 0);

    reset(); REAL(actor, 0x180) = 0.5f;
    WORD(actor, 0xD04) = 4; REAL(actor, 0x184) = 7; af_v3_player_fan_finish(actor, game);
    assert(!settled && !requests && !wait_requests);
    REAL(actor, 0x184) = 7.5f; af_v3_player_fan_finish(actor, game);
    assert(settled == 1 && bee == 1 && !requests);
    REAL(actor, 0x184) = 8; held_a = 1; af_v3_player_fan_finish(actor, game);
    assert(requests == 1 && WORD(actor, 0xD58) == 0 && !wait_requests && !walk_requests);
    reset(); REAL(actor, 0x184) = 8.5f; move_y = 0.3f; af_v3_player_fan_finish(actor, game);
    assert(walk_requests == 1 && wait_requests == 1 && settled == 1);
    reset(); REAL(actor, 0x184) = 8.5f; af_v3_player_fan_finish(actor, game);
    assert(wait_requests == 1 && !walk_requests && settled == 1 && WORD(actor, 0xD00) == 7);
    reset(); REAL(actor, 0x184) = 8.5f; move_x = 0.2f; af_v3_player_fan_finish(actor, game);
    assert(walk_requests == 1 && wait_requests == 1 && events[0] == 8 && events[1] == 6 && events[2] == 9);
    assert(WORD(actor, 0xD00) == 8 && WORD(actor, 0xD04) == 1 && WORD(actor, 0xD08) == 1);
    reset(); REAL(actor, 0x184) = 1; af_v3_player_fan_main(actor, game);
    assert(REAL(actor, 0x184) == 2 && sound_calls == 1 && event_count == 9);
    for (int i = 0; i < 9; ++i) assert(events[i] == i+11);
    event_count = 0; stopped = 1; af_v3_player_fan_main(actor, game);
    assert(sound_calls == 1 && event_count == 8 && events[4] == 16);
    event_count = 0; stopped = 0; af_v3_player_fan_main(actor, game);
    assert(REAL(actor, 0x184) == 3 && sound_calls == 1);
    reset(); REAL(actor, 0x184) = 7; WORD(actor, 0xD04) = 4;
    af_v3_player_fan_main(actor, game);
    assert(REAL(actor, 0x184) == 8 && bee == 1 && settled == 1 && !sound_calls);
    event_count = 0; af_v3_player_fan_main(actor, game);
    assert(wait_requests == 1 && WORD(actor, 0xD00) == 7);
    assert(REAL(actor, 0x184) == 1 && !sound_calls);
    reset(); REAL(actor, 0x184) = 7; WORD(actor, 0xD04) = 4; held_a = 1;
    af_v3_player_fan_main(actor, game);
    assert(bee == 1 && requests == 1 && WORD(actor, 0xD00) == 109 && !WORD(actor, 0xD58));
    reset(); REAL(actor, 0x184) = 7; WORD(actor, 0xD04) = 4; move_x = 0.25f;
    af_v3_player_fan_main(actor, game);
    assert(bee == 1 && walk_requests == 1 && WORD(actor, 0xD00) == 8);
    struct { u8 padding[0x298]; u32 *cursor; } graph;
    struct { void *graph; } draw_game = { &graph };
    u32 display[6] = { 0x12345678, 0, 0, 0x87654321, 0, 0 };
    graph.cursor = display+1; reset(); model_pointer = 0x06001230;
    WORD(actor, 0xDEC) = 1; WORD(actor, 0xDE0) = 40; WORD(actor, 0xF44) = 1;
    af_v3_player_draw_static_item(actor, &draw_game);
    assert(model_shape == 40 && graph.cursor == display+3 && !WORD(actor, 0xF44));
    assert(display[0] == 0x12345678 && display[1] == 0xDE000000 && display[2] == model_pointer);
    assert(display[3] == 0x87654321);
    model_pointer = 0; WORD(actor, 0xF44) = 1;
    af_v3_player_draw_static_item(actor, &draw_game);
    assert(graph.cursor == display+3 && !WORD(actor, 0xF44));
    for (int bank = -1; bank <= 2; bank += 3) {
        WORD(actor, 0xDEC) = bank; WORD(actor, 0xF44) = 1; model_shape = -1;
        af_v3_player_draw_static_item(actor, &draw_game);
        assert(model_shape == -1 && graph.cursor == display+3 && !WORD(actor, 0xF44));
    }
    puts("shared player fan controls, native timing, per-frame flow, and sound pass");
    return 0;
}
