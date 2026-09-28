#ifndef AF_V3_NPC_DMA_H
#define AF_V3_NPC_DMA_H
typedef struct {unsigned int start,end,physical;} AFNpcDmaRow;
typedef struct {unsigned int magic,version,count,stride;AFNpcDmaRow rows[8];} AFNpcDma;
typedef struct {
    unsigned int vrom;void *vram;unsigned int bytes;
    const char *filename;unsigned int line,unused;void *queue,*message;
} AFNpcDmaRequest;
extern const AFNpcDma af_v3_npc_dma;
void af_v3_npc_dma_request(AFNpcDmaRequest *);
int af_v3_npc_dma_init(void);
#endif
