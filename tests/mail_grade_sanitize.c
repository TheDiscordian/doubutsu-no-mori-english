/* Exact-sized input allocations expose reads outside the declared body. */
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "mail/grade.h"

int main(void) {
    unsigned int size, pattern, i, random = 71493;
    for (size = 0; size <= AF_MAIL_GRADE_MAX; ++size) {
        unsigned char *body = malloc(size ? size : 1);
        unsigned char *copy = malloc(size ? size : 1);
        assert(body && copy);
        for (pattern = 0; pattern < 8; ++pattern) {
            AfMailGrade grade;
            int words, rate, total = 0;
            for (i = 0; i < size; ++i) {
                random = random*1664525u+1013904223u;
                body[i] = pattern == 0 ? ' ' : pattern == 1 ? 'x'
                    : pattern == 2 ? '.' : pattern == 3 ? (i ? 'x' : '.')
                    : pattern == 4 ? (unsigned char)i
                    : pattern == 5 ? (unsigned char)(random>>24)
                    : (unsigned char)" .?!,aeiI'XAbcothen\xcd\x85"[(random>>16)%22];
            }
            memcpy(copy,body,size);
            assert(af_mail_grade(&grade,body,size));
            rate = af_mail_word_rate(&words,body,size);
            assert(rate >= 0 && rate <= 100 && words >= 0);
            for (i = 0; i < 7; ++i) total += grade.components[i];
            assert(grade.total == total);
            assert(grade.rank == (total >= 100 ? 1u : total < 50 ? 0u : 2u));
            assert(!memcmp(copy,body,size));
        }
        free(copy);
        free(body);
    }
    return 0;
}
