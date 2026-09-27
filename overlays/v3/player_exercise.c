#include "player_exercise.h"

void af_v3_exercise_init(AFExercise *s, unsigned int sound_frame) {
    for (unsigned int i = 0; i < 8; ++i) s->ring[i] = -1;
    s->head = s->hold = 0;
    s->continuation = -1;
    s->timer = 0.0f;
    s->command = s->settled = s->late = 0;
    s->skip = 1;
    s->old_sound_frame = sound_frame;
}

void af_v3_exercise_push(AFExercise *s, int command) {
    if (command < -1 || command > 8) command = -1;
    if (command >= 0 && s->ring[s->head] == command && s->hold < 50) {
        ++s->hold;
        return;
    }
    s->head = (s->head + 7) & 7;
    s->ring[s->head] = (signed char)command;
    s->hold = 0;
}

int af_v3_exercise_match(const AFExercise *s, const AFExercisePattern *data, float *timer) {
    int next = (unsigned int)s->continuation < 18u ? data[s->continuation].next : -1;
    *timer = 0.0f;
    for (int i = 0; i < 18; ++i) {
        const AFExercisePattern *p = data + i;
        if (next >= 0 && i != next) continue;
        if (!p->length || p->length > 8) continue;
        int j;
        for (j = 0; j < p->length; ++j) {
            int key = s->ring[(s->head + j) & 7];
            if (key < 0 || key != p->keys[p->length - 1 - j]) break;
        }
        if (j == p->length) {
            if (p->next >= 0) *timer = 6.0f;
            return i;
        }
    }
    return -1;
}

int af_v3_exercise_check(AFExercise *s, const AFExercisePattern *data, int able,
                         int skip_request, const AFExerciseCalls *calls) {
    if (!able) return 0;
    s->timer -= 1.0f;
    if (s->timer < 0.0f) s->timer = 0.0f;
    float timer;
    int found = af_v3_exercise_match(s, data, &timer);
    if (found >= 0 && (s->continuation < 0 || s->timer > 0.0f)) {
        s->continuation = found;
        s->timer = timer;
    }
    if (!skip_request && s->continuation >= 0 && s->timer <= 0.0f)
        return calls->request(calls->context, s->continuation, 0.0f, 4) != 0;
    return 0;
}

void af_v3_exercise_wait_setup(AFExercise *s, int flags) {
    s->skip = (flags & 4) == 0;
    if (s->skip) {
        s->continuation = -1;
        s->timer = 0.0f;
    }
}

void af_v3_exercise_input(AFExercise *s, int able, int command) {
    af_v3_exercise_push(s, able && !s->skip ? command : -1);
    s->skip = 0;
}

unsigned int af_v3_exercise_setup(AFExercise *s, const AFExercisePattern *data, int command) {
    if ((unsigned int)command >= 18u) command = 0;
    s->command = command;
    s->skip = 1;
    s->settled = s->late = 0;
    s->continuation = -1;
    s->timer = 0.0f;
    return data[command].animation;
}

float af_v3_exercise_speed(const AFExercise *s, const AFExercisePattern *data,
                          float speed, unsigned int now, int radio_status, int tempo) {
    float target = radio_status == 0 ? tempo * 0.012f : 0.0f;
    if (target <= 0.0f) target = 0.5f;
    if (now != s->old_sound_frame) {
        /* Preserve the donor's wrap convention, including the missing +1. */
        unsigned int delta = now > s->old_sound_frame ? now - s->old_sound_frame
            : 0xFFFFFFFFu - s->old_sound_frame + now;
        if (delta > 5u) delta = 5u;
        target *= (int)delta;
    }
    unsigned int command = (unsigned int)s->command < 18u ? (unsigned int)s->command : 0u;
    target *= data[command].speed;
    if (speed != target) {
        float step = 0.3f * (target - speed);
        if (step > 0.5f) step = 0.5f;
        else if (step < -0.5f) step = -0.5f;
        speed += step;
    }
    return speed;
}

void af_v3_exercise_finish(AFExercise *s, const AFExercisePattern *data, int able,
                          float frame, float end, float speed, int ended,
                          const AFExerciseCalls *calls) {
    if (!s->late) {
        if (frame >= end - 24.0f) s->late = 1;
    } else {
        af_v3_exercise_check(s, data, able, 1, calls);
    }
    if (!s->settled) {
        if (frame >= end - 0.5f) {
            calls->settle(calls->context);
            calls->bee_attack(calls->context);
            s->settled = 1;
        }
    } else if (ended) {
        if ((unsigned int)s->continuation < 18u && s->timer <= 0.0f)
            calls->request(calls->context, s->continuation, speed, 4);
        else
            calls->wait(calls->context, -5.0f, 4, 1);
    }
}

int af_v3_exercise_buttons(unsigned int held, int forbidden) {
    if (forbidden) return -1;
    /* N64 C buttons substitute the donor's eight C-stick directions. Opposite
       pairs cancel; camera eligibility must be suppressed only while able. */
    int x = ((held & 1u) != 0) - ((held & 2u) != 0);
    int y = ((held & 8u) != 0) - ((held & 4u) != 0);
    if (y > 0) return x > 0 ? 7 : x < 0 ? 8 : 6;
    if (y < 0) return x > 0 ? 4 : x < 0 ? 5 : 3;
    return x > 0 ? 1 : x < 0 ? 2 : 0;
}
