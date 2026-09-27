#ifndef AF_V3_PLAYER_EXERCISE_NATIVE_H
#define AF_V3_PLAYER_EXERCISE_NATIVE_H
#include "player_exercise.h"

/* Transient tail of the player actor; never part of a saved player record. */
#define AF_EXERCISE_STATE_OFFSET 0x13B0u
#define AF_EXERCISE_PLAYER_BYTES 0x13E0u
extern const AFExercisePattern af_v3_exercise_patterns[18];

void af_v3_exercise_native_init(void *, void *);
void af_v3_exercise_native_after(void *, void *);
void af_v3_exercise_native_wait_setup(void *, void *);
void af_v3_exercise_native_wait(void *, void *);
void af_v3_exercise_native_setup(void *, void *);
void af_v3_exercise_native_main(void *, void *);
int af_v3_exercise_native_camera(void *);
int af_v3_exercise_native_able(void *);
int af_v3_exercise_native_input(void *, void *);
unsigned int af_v3_exercise_native_clock(void);
int af_v3_exercise_native_tempo(int *);

#ifndef __mips__
void *af_test_exercise_resolve(unsigned int);
void *af_test_exercise_memory(unsigned int);
#endif
#endif
