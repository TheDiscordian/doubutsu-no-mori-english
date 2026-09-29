#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/resource_dma.h"
static unsigned int last_source,last_size,physical_calls,virtual_calls;
static void *last_dest;
static int status;
int af_test_resource_pi(unsigned int source,void *dest,unsigned int bytes) {
    last_source=source;last_dest=dest;last_size=bytes;physical_calls++;return status;
}
static int virtual_read(void *dest,unsigned int source,unsigned int bytes) {
    last_source=source;last_dest=dest;last_size=bytes;virtual_calls++;return status;
}
int main(void) {
    char data[144];
    for(int mode=0;mode<2;mode++) {
        status=mode?-7:0;
        assert(af_v3_resource_read(data,0x837C2C30u,144,virtual_read)==status);
        assert(last_source==0x037C2C30u && last_dest==data && last_size==144);
        assert(physical_calls==(unsigned int)mode+1 && virtual_calls==(unsigned int)mode);
        assert(af_v3_resource_read(data,0x02592EE0u,144,virtual_read)==status);
        assert(last_source==0x02592EE0u && last_dest==data && last_size==144);
    }
    const unsigned int invalid[][2]={{0x84000000u,2},{0x83FFFFF0u,32},
        {0xC37C2C30u,144},{0x837C2C31u,144},{0x837C2C30u,1},{0x837C2C30u,0}};
    for(unsigned int i=0;i<sizeof(invalid)/sizeof(*invalid);i++)
        assert(af_v3_resource_read(data,invalid[i][0],invalid[i][1],virtual_read)==-1);
    assert(physical_calls==2 && virtual_calls==2);
    puts("Resource DMA routing, argument order, failures, and bounds passed");
}
