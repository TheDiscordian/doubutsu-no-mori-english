#include <stdint.h>
#include <string.h>
struct Clothing { unsigned short item, index; unsigned int vrom;
    unsigned short price; unsigned char enabled, reserved, name[16]; unsigned int padding; };
struct Clothing af_v3_clothing;
unsigned char texture[544], palette[64];
unsigned int async_calls, sync_calls, create_calls, receive_calls, invalid_calls;
unsigned int sources[4], sizes[4];
int receive_result;
void *last_queue;
void *af_v3_clothing_destination(unsigned char *bank) {
    unsigned int token;
    memcpy(&token, bank+4, 4);
    return token == 1 ? texture+16 : token == 2 ? palette+16 : 0;
}
void af_v3_clothing_queue_create(void *queue, void *messages, int count) {
    ++create_calls;
    if ((unsigned char *)messages != (unsigned char *)queue+0x18 || count != 1) ++invalid_calls;
    last_queue = queue;
}
int af_v3_clothing_queue_receive(void *queue, void *message, int blocking) {
    ++receive_calls;
    if (!queue || message || blocking) ++invalid_calls;
    return receive_result;
}
int af_v3_clothing_dma(void *out, unsigned int vrom, unsigned int size) {
    ++sync_calls;
    if (!out || (size != 32 && size != 512)) { ++invalid_calls; return -1; }
    memset(out, (vrom >> 5) & 255, size);
    return 0;
}
void af_v3_clothing_dma_async(void *request, void *out, unsigned int vrom, unsigned int size,
        int unknown, void *queue, void *message, const char *file, int line) {
    if (async_calls >= 4) { ++invalid_calls; return; }
    sources[async_calls] = vrom; sizes[async_calls++] = size;
    if ((unsigned char *)queue != (unsigned char *)request+0x20 || queue != last_queue
            || unknown || message || !file || line != 1) ++invalid_calls;
    memcpy(request, &vrom, 4);
    if (!out || (size != 32 && size != 512)) { ++invalid_calls; return; }
    memset(out, (vrom >> 5) & 255, size);
}
