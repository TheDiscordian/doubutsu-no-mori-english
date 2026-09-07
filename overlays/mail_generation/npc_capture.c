#include "npc_capture.h"
#include "digest.h"

#define READY 0x41464353u

static const unsigned int word_bases[11] = {
    0x314u,0x334u,0x2F4u,0x219u,0x1E5u,0x354u,0x374u,0x394u,0x3D4u,0x3F4u,0x3B4u
};
static const unsigned int group_bases[12] = {32u,64u,0u,96u,128u,160u,224u,256u,192u,288u,320u,352u};

#ifdef __mips__
typedef char sources_size_check[sizeof(AfNpcMailSources) == 12 ? 1 : -1];
typedef char capture_work_size_check[sizeof(AfNpcMailCaptureWork) == 444 ? 1 : -1];
typedef char capture_offset_check[__builtin_offsetof(AfNpcMailCaptureWork,capture) == 44 ? 1 : -1];
typedef char selection_offset_check[__builtin_offsetof(AfNpcMailCaptureWork,selection) == 412 ? 1 : -1];
static const unsigned char *town(void) { return ((const unsigned char *(*)(void))0x800950D8u)(); }
#else
extern const unsigned char *af_npc_test_town(void);
#define town af_npc_test_town
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    return x <= y ? y-x < as : x-y < bs;
}

static unsigned int u16(const unsigned char *data) {
    return ((unsigned int)data[0]<<8)|data[1];
}

static int hash(const unsigned char *data, unsigned int size, const unsigned int expected[8]) {
    unsigned char digest[32];
    unsigned int i;
    if (!af_mail_source_digest(digest,data,size)) return 0;
    for (i = 0; i < 32u; ++i)
        if (digest[i] != (unsigned char)(expected[i>>2]>>(24u-8u*(i&3u)))) return 0;
    return 1;
}

int af_npc_mail_sources_init(AfNpcMailSources *out, const unsigned char *words, unsigned int word_size,
                             const unsigned char *aliases, unsigned int alias_size) {
    static const unsigned int word_hash[8] = {
        0x698e26d2u,0x1c20eddcu,0xc2576631u,0x7aa52024u,0x949f4ebau,0x51db99d7u,0x3d58d46fu,0x6c5a12c1u
    };
    static const unsigned int alias_hash[8] = {
        0xa79b6bc3u,0xc5b36c7cu,0xe2bcea55u,0x932ccdf4u,0xce694608u,0xe5dcfb89u,0x6226a24du,0x368bf5d6u
    };
    if (!out || ((__UINTPTR_TYPE__)out & (__alignof__(AfNpcMailSources)-1u))
            || !words || !aliases || word_size != AF_NPC_WORD_BYTES || alias_size != AF_NPC_ALIAS_BYTES
            || overlap(out,sizeof(*out),words,word_size) || overlap(out,sizeof(*out),aliases,alias_size)
            || !hash(words,word_size,word_hash) || !hash(aliases,alias_size,alias_hash))
        return 0;
    out->words = words; out->aliases = aliases; out->ready = READY;
    return 1;
}

static int output_valid(AfMailField *out, const AfNpcMailSources *sources) {
    return out && sources && sources->ready == READY && sources->words && sources->aliases
        && !overlap(out,sizeof(*out),sources,sizeof(*sources))
        && !overlap(out,sizeof(*out),sources->words,AF_NPC_WORD_BYTES)
        && !overlap(out,sizeof(*out),sources->aliases,AF_NPC_ALIAS_BYTES);
}

static void field(AfMailField *out, const unsigned char *text, unsigned int size, unsigned int width) {
    AfMailField value;
    unsigned int i;
    value.length = (unsigned char)width; value.article = 0;
    for (i = 0; i < 16u; ++i) value.text[i] = i < size ? text[i] : i < width ? ' ' : 0;
    for (i = 0; i < sizeof(value); ++i) ((unsigned char *)out)[i] = ((unsigned char *)&value)[i];
}

int af_npc_mail_source_word(AfMailField *out, const AfNpcMailSources *sources, unsigned int slot, unsigned int id) {
    unsigned int index;
    const unsigned char *row;
    if (!output_valid(out,sources) || slot < 3u || slot > 13u || id < word_bases[slot-3u]
            || id-word_bases[slot-3u] >= 32u) return 0;
    index = (slot-3u)*32u+id-word_bases[slot-3u];
    row = sources->words+64u+index*32u;
    if (u16(row) != id || row[4] != slot || !row[5] || row[5] > 16u || row[6] || row[7]) return 0;
    /* The English native string loader pads its sixteen-byte temporary with
     * spaces before the handbill setter captures the complete field.
     */
    field(out,row+8u,row[5],16u);
    return 1;
}

int af_npc_mail_source_name(AfMailField *out, const AfNpcMailSources *sources, unsigned int npc) {
    unsigned int i;
    const unsigned char *row;
    if (!output_valid(out,sources) || npc < 0xE000u || npc >= 0xE0D8u) return 0;
    for (i = 0; i < 394u; ++i) {
        row = sources->aliases+64u+i*16u;
        if (u16(row+6u) == npc-0xE000u) { field(out,row+8u,8u,8u); return 1; }
    }
    return 0;
}

int af_npc_mail_source_alias(AfMailField *out, const AfNpcMailSources *sources, const unsigned char *key) {
    unsigned int low = 0, high = 394u, mid, i;
    const unsigned char *row;
    if (!output_valid(out,sources) || !key) return 0;
    while (low < high) {
        mid = low+(high-low)/2u;
        row = sources->aliases+64u+mid*16u;
        for (i = 0; i < 6u && row[i] == key[i]; ++i) {}
        if (i == 6u) { field(out,row+8u,8u,8u); return 1; }
        if (row[i] < key[i]) low = mid+1u;
        else high = mid;
    }
    return 0;
}

static int invalid(AfNpcMailCaptureWork *work) { work->failed = 1; return 0; }

static void capture(AfNpcMailCaptureWork *work, unsigned int slot, const unsigned char *value, unsigned int length) {
    if (!af_mail_capture_set(&work->capture,slot,value,length,0)) work->failed = 1;
}

int af_npc_mail_capture_event(AfNpcMailSession *session, unsigned int event, const void *data, unsigned int value) {
    AfNpcMailCaptureWork *work = (AfNpcMailCaptureWork *)session;
    const AfNpcMailPrepare *args = (const AfNpcMailPrepare *)data;
    const unsigned char *animal = (const unsigned char *)data;
    const unsigned int *ids = (const unsigned int *)data;
    AfMailField selected;
    unsigned int i, slot, looks, base;
    if (!session) return 0;
    if (event == AF_NPC_PREPARE_BEGIN) {
        if (work->phase || work->failed || !args || value != sizeof(*args)
                || args->player != session->player || args->animal != session->animal || args->remail != session->remail
                || !session->player || (!session->animal && !session->remail) || !session->stage
                || session->condition > 1u || session->foreign > 1u || session->initial_capital > 1u
                || work->sources.ready != READY) return invalid(work);
        af_mail_capture_reset(&work->capture);
        work->capture.capital = session->initial_capital;
        work->phase = 1; work->words_seen = 0; work->names_seen = 0;
        capture(work,0,session->player,6);
        if (session->remail) {
            if (af_npc_mail_source_alias(&selected,&work->sources,session->remail+4u))
                capture(work,1,selected.text,selected.length);
            else invalid(work);
            capture(work,14,session->remail+10u,6);
            capture(work,15,town(),6);
        }
        return !work->failed;
    }
    if (work->failed) return 0;
    if (event == AF_NPC_SENDER_NAME || event == AF_NPC_OTHER_NAME) {
        slot = event == AF_NPC_SENDER_NAME ? 1u : 2u;
        if (work->phase != 1u || work->words_seen || value || !animal
                || (slot == 1u && (session->remail || animal != session->animal || work->names_seen))
                || (slot == 2u && work->names_seen != (session->remail ? 0u : 1u))
                || !af_npc_mail_source_name(&selected,&work->sources,u16(animal))) return invalid(work);
        capture(work,slot,selected.text,selected.length);
        ++work->names_seen;
        return !work->failed;
    }
    if (event == AF_NPC_WORD) {
        slot = work->words_seen+3u;
        if (work->phase != 1u || data || work->words_seen >= 11u
                || work->names_seen != (session->remail ? 1u : 2u)
                || !af_npc_mail_source_word(&selected,&work->sources,slot,value)) return invalid(work);
        capture(work,slot,selected.text,selected.length);
        ++work->words_seen;
        return !work->failed;
    }
    if (event == AF_NPC_PREPARE_END) {
        if (work->phase != 1u || !args || value != sizeof(*args) || work->words_seen != 11u
                || args->player != session->player || args->animal != session->animal || args->remail != session->remail
                || work->capture.valid != (session->remail ? 0xFFFFu : 0x3FFFu)) return invalid(work);
        work->phase = 2;
        return 1;
    }
    if (work->phase != 2u || !data) return invalid(work);
    looks = session->remail ? session->remail[16]&127u : session->animal[11];
    if (looks >= 6u) return invalid(work);
    work->selection.catalog = AF_MAIL_CATALOG_ID;
    work->selection.reserved = 0;
    if (event == AF_NPC_COMPOSITE && value == 5u && session->condition == 1u) {
        base = group_bases[session->foreign*6u+looks];
        for (i = 0; i < 5u; ++i) if (ids[i] < base || ids[i]-base >= 32u) return invalid(work);
        work->selection.kind = 1;
        for (i = 0; i < 5u; ++i) work->selection.templates[i] = (unsigned short)ids[i];
    } else if (event == AF_NPC_CLASSIC && value == 1u && !session->condition) {
        base = (session->foreign ? 216u : 197u)+looks*3u;
        if (ids[0] < base || ids[0]-base >= 3u) return invalid(work);
        work->selection.kind = 0;
        work->selection.templates[0] = (unsigned short)ids[0];
        for (i = 1; i < 5u; ++i) work->selection.templates[i] = 0;
    } else return invalid(work);
    work->phase = 3;
    return 1;
}
