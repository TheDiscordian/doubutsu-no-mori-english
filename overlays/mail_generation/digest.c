#include "digest.h"

static unsigned int rotate(unsigned int value, unsigned int bits) {
    return (value >> bits) | (value << (32u-bits));
}

static void block(unsigned int state[8], const unsigned char input[64]) {
    static const unsigned int constants[64] = {
        0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
        0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
        0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
        0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
        0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
        0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
        0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
        0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
    };
    unsigned int words[16],a,b,c,d,e,f,g,h,i,x,y,t,u;
    a = state[0]; b = state[1]; c = state[2]; d = state[3];
    e = state[4]; f = state[5]; g = state[6]; h = state[7];
    for (i = 0; i < 64u; ++i) {
        if (i < 16u)
            words[i] = ((unsigned int)input[4u*i] << 24) | ((unsigned int)input[4u*i+1u] << 16)
                     | ((unsigned int)input[4u*i+2u] << 8) | input[4u*i+3u];
        else {
            x = words[(i+1u)&15u]; y = words[(i+14u)&15u];
            words[i&15u] += (rotate(x,7)^rotate(x,18)^(x>>3)) + words[(i+9u)&15u]
                         + (rotate(y,17)^rotate(y,19)^(y>>10));
        }
        t = h+(rotate(e,6)^rotate(e,11)^rotate(e,25))+((e&f)^(~e&g))+constants[i]+words[i&15u];
        u = (rotate(a,2)^rotate(a,13)^rotate(a,22))+((a&b)^(a&c)^(b&c));
        h = g; g = f; f = e; e = d+t; d = c; c = b; b = a; a = t+u;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

int af_mail_source_digest(unsigned char output[32], const unsigned char *input, unsigned int size) {
    unsigned int state[8];
    unsigned char tail[64];
    unsigned int at = 0, remaining, i, high, low;
    __UINTPTR_TYPE__ out = (__UINTPTR_TYPE__)output, in = (__UINTPTR_TYPE__)input;
    if (!output || (!input && size) || size > 0x100000u
            || (size && (out <= in ? in-out < 32u : out-in < size)))
        return 0;
    state[0] = 0x6a09e667u; state[1] = 0xbb67ae85u; state[2] = 0x3c6ef372u; state[3] = 0xa54ff53au;
    state[4] = 0x510e527fu; state[5] = 0x9b05688cu; state[6] = 0x1f83d9abu; state[7] = 0x5be0cd19u;
    while (size-at >= 64u) { block(state,input+at); at += 64u; }
    remaining = size-at;
    for (i = 0; i < 64u; ++i) tail[i] = i < remaining ? input[at+i] : 0;
    tail[remaining] = 0x80u;
    if (remaining >= 56u) {
        block(state,tail);
        for (i = 0; i < 64u; ++i) tail[i] = 0;
    }
    high = size>>29; low = size<<3;
    for (i = 0; i < 4u; ++i) {
        tail[56u+i] = (unsigned char)(high>>(24u-8u*i));
        tail[60u+i] = (unsigned char)(low>>(24u-8u*i));
    }
    block(state,tail);
    for (i = 0; i < 32u; ++i) output[i] = (unsigned char)(state[i>>2]>>(24u-8u*(i&3u)));
    return 1;
}
