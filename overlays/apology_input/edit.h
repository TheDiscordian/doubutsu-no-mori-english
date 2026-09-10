#ifndef AF_APOLOGY_EDIT_H
#define AF_APOLOGY_EDIT_H

#define AF_APOLOGY_BYTES 10u
#define AF_APOLOGY_SUN 0x80A7u
#define AF_APOLOGY_SKULL 0x80BAu

struct af_apology_draft {
    unsigned char text[AF_APOLOGY_BYTES];
    unsigned char length, cursor;
};

enum af_apology_command {
    AF_APOLOGY_LEFT=1, AF_APOLOGY_DOWN, AF_APOLOGY_UP, AF_APOLOGY_RIGHT,
    AF_APOLOGY_DONE, AF_APOLOGY_BACKSPACE, AF_APOLOGY_EXCHANGE, AF_APOLOGY_INSERT
};
enum af_apology_result {
    AF_APOLOGY_ARGUMENT=-2, AF_APOLOGY_FULL=-1, AF_APOLOGY_UNCHANGED=0,
    AF_APOLOGY_CHANGED=1, AF_APOLOGY_FINISHED=2
};

int af_apology_valid(const struct af_apology_draft *);
int af_apology_edit(struct af_apology_draft *, int command, int code);

#endif
