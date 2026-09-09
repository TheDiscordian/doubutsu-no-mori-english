#include "reader.h"
#include "../../runtime/notice/treasure.h"

/* Both decoders publish only complete output. A rejected initial identity does
 * not read the catalogue, and the treasure path reuses the same workspace.
 * Keep the initial-only reader source intact for its retained native evidence.
 */
int af_notice_complete_restore(AfNoticeText *output, const unsigned char *input,
                                 unsigned int size, AfNoticeWorkspace *work) {
    return af_notice_initial_restore(output, input, size, work)
        || af_notice_treasure_restore(output, input, size, work);
}

#define af_notice_initial_restore af_notice_complete_restore
#include "reader.c"
