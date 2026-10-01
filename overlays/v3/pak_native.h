#ifndef AF_V3_PAK_NATIVE_H
#define AF_V3_PAK_NATIVE_H
#include "pak_codec.h"

/* Two physical notes per logical kind allow a new note to be committed without
 * overwriting the last successful write. Original native notes are read-only.
 * These are replacements for the native shared write/read/status entries, not
 * replacements for native Private, Passport, or backup structure dimensions. */
enum {
    AF_PI_PAGE=256, AF_PI_NOTE=AF_PAK_MAX_NOTE,
    AF_PI_RAW=AF_PAK_BACKUP_NOTE+AF_PAK_MAX_RECORDS,
    AF_PI_SCRATCH=2*AF_PI_NOTE+AF_PI_RAW
};
typedef struct {
    af_pak_u8 *notes[2],*raw;
    af_pak_u32 *hash;
    const af_pak_u8 *binding;
} AFPIWorkspace;
int af_v3_pak_native_write(void *info,const void *native);
int af_v3_pak_native_read(void *info,void *native);
int af_v3_pak_native_status(int *status,int kind,void *info,void *backup);

/* Integration providers. Acquire owns the existing save scratch/hash until
 * release; it checks guards and save state before setting their shared busy
 * flag. Records remain outside the borrowed buffers. Validate is read-only;
 * publish cannot fail and copies an already validated record before release.
 * Publication is enabled only by the arrival/return lifecycle wrapper; ordinary
 * status, identity, and nonce reads must not replace a visitor's newer progress
 * with the older departure snapshot. Legacy validation explicitly handles the
 * existing creature capsule. Providers use checked references resolved before
 * the loan, not data getters which require the save workspace to be idle. */
int af_pi_workspace_acquire(AFPIWorkspace *);
int af_pi_workspace_release(void);
int af_pi_record_export(unsigned kind,const af_pak_u8 *native,AFPakInput *);
int af_pi_record_validate(const AFPakView *);
int af_pi_legacy_validate(unsigned kind,const af_pak_u8 *native);
void af_pi_record_publish(const AFPakView *);
void af_pi_legacy_publish(unsigned kind,const af_pak_u8 *native);

/* Unchanged native providers; the installer binds their checked addresses. */
void *af_pi_lock(void);
void af_pi_unlock(void *);
int af_pi_open(void *info),af_pi_make(void *info),af_pi_num(void *info);
int af_pi_free(void *info);
unsigned af_pi_file_state(void *pfs,void *state);
int af_pi_load(void *pfs,int offset,int bytes,af_pak_u8 *);
int af_pi_save(void *pfs,int offset,int bytes,const af_pak_u8 *);
int af_pi_delete(void *pfs,void *state);
int af_pi_null_identity(const af_pak_u8 *);
#endif
