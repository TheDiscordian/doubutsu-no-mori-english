#ifndef AF_V3_PLAYER_EXERCISE_H
#define AF_V3_PLAYER_EXERCISE_H

/* Complete gesture records are derived from the donor's relocated tables. */
typedef struct {
    signed char keys[8];
    unsigned char length;
    signed char next;
    unsigned short animation;
    float speed;
} AFExercisePattern;

typedef struct {
    signed char ring[8];
    int head, hold, continuation;
    float timer;
    int command, skip, settled, late;
    unsigned int old_sound_frame;
} AFExercise;

typedef struct {
    void *context;
    int (*request)(void *, int command, float speed, int priority);
    void (*wait)(void *, float morph, int flags, int priority);
    void (*settle)(void *);
    void (*bee_attack)(void *);
} AFExerciseCalls;

void af_v3_exercise_init(AFExercise *, unsigned int sound_frame);
void af_v3_exercise_push(AFExercise *, int command);
int af_v3_exercise_match(const AFExercise *, const AFExercisePattern *, float *timer);
int af_v3_exercise_check(AFExercise *, const AFExercisePattern *, int able,
                         int skip_request, const AFExerciseCalls *);
void af_v3_exercise_wait_setup(AFExercise *, int flags);
void af_v3_exercise_input(AFExercise *, int able, int command);
unsigned int af_v3_exercise_setup(AFExercise *, const AFExercisePattern *, int command);
float af_v3_exercise_speed(const AFExercise *, const AFExercisePattern *,
                          float speed, unsigned int now, int radio_status, int tempo);
void af_v3_exercise_finish(AFExercise *, const AFExercisePattern *, int able,
                          float frame, float end, float speed, int ended,
                          const AFExerciseCalls *);
int af_v3_exercise_buttons(unsigned int held, int forbidden);

#endif
