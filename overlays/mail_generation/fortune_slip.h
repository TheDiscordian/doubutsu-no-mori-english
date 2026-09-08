#ifndef AF_FORTUNE_SLIP_H
#define AF_FORTUNE_SLIP_H

#include "generate.h"

#define AF_FORTUNE_WORD_BYTES (68u * 16u)

/* Four native RNG results, native outcome (without the GC permutation), and
 * the original three-way template draw. No random calls occur in this API.
 */
typedef struct {
    unsigned char phrases[4];
    unsigned char outcome;
    unsigned char template_index;
    unsigned char reserved[2];
} AfFortuneSlipChoice;

typedef struct {
    AfMailCapture capture;
    AfMailSelection selection;
    unsigned char mail[164];
    AfMailGenerateWork generation __attribute__((aligned(16)));
} AfFortuneSlipWork;

/* Complete transaction on a caller-prepared native letter. Native identity,
 * attachment, and other metadata are retained; received status, fortune type,
 * paper 25, split marker, and full snapshot are published only after validation.
 * No native actor, inventory, RNG, money, luck, or animation is changed here.
 * Caller supplies immutable verified words and owns all buffer lifetimes.
 * Rejection retains destination, selection, words, and capitalization state.
 */
int af_fortune_slip_create(unsigned char *mail, unsigned int size,
    const AfFortuneSlipChoice *choice, const unsigned char *words,
    unsigned int word_bytes, unsigned int *capital, AfFortuneSlipWork *work);

#endif
