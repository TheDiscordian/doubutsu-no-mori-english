#include "reader.h"
#include "../../runtime/notice/treasure.h"
#include "../../runtime/notice/seasonal.h"

/* Preserve all existing saved identities. Every decoder leaves output intact
 * on rejection, so the shared cache publishes only a complete matching body.
 */
int af_notice_complete_restore(AfNoticeText *output, const unsigned char *input,
                                 unsigned int size, AfNoticeWorkspace *work) {
    return af_notice_initial_restore(output, input, size, work)
        || af_notice_treasure_restore(output, input, size, work)
        || af_notice_seasonal_restore(output, input, size, work);
}

#define af_notice_initial_restore af_notice_complete_restore
#include "reader.c"
