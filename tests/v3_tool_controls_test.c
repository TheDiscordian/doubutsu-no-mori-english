#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include "../overlays/v3/tool_controls.c"
static int supplied, calls, expected_action;
static char actor;
int af_test_visible_tool_kind(void *p, int action) {
    assert(p == &actor && action == expected_action);
    ++calls;
    return supplied;
}
static void check(int kind, int expected) {
    supplied = kind;
    for (int action = -1; action < 121; ++action) {
        expected_action = action;
        int before = calls;
        assert(af_v3_player_control_kind(&actor, action) == expected);
        assert(calls == before + 1);
    }
}
int main(void) {
    for (int i = -128; i < 128; ++i) {
        int expected = i;
        if (i >= 36 && i < 115) {
            if (i <= 44) expected = 0;
            else if (i <= 46) expected = 1;
            else if (i <= 86) expected = 2;
            else if (i <= 88) expected = 34;
            else if (i <= 90) expected = 35;
            else expected = 2;
        }
        check(i, expected);
    }
    check(INT_MAX, INT_MAX);
    check(INT_MIN, INT_MIN);
    puts("Shared tool predicates retain kinds, permission calls, and input families: pass");
}
