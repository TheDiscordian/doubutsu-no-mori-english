/* Complete per-frame face sequences for installed imported player motions. */
typedef unsigned int u32;
#ifdef __mips__
#define native_eye ((const u32 *)0x8010C0E8u)
#define native_mouth ((const u32 *)0x8010C2F0u)
#define faces ((const u32 *)0x804B4700u)
#else
extern u32 af_test_native_eye[130], af_test_native_mouth[130], af_test_player_faces[318];
#define native_eye af_test_native_eye
#define native_mouth af_test_native_mouth
#define faces af_test_player_faces
#endif

static u32 imported_face(int index, u32 column) {
    u32 slot=(u32)index-130u;
    if (slot>=157u || faces[0]!=0x41465046u || faces[1]!=1u ||
            faces[2]!=157u || faces[3]!=8u) return 0;
    u32 address=faces[4+slot*2+column];
    return address>=0x804B4C00u && address<0x804B4F00u ? address : 0;
}

u32 af_v3_player_eye_sequence(int index) {
    return (u32)index<130u ? native_eye[index] : imported_face(index,0);
}

u32 af_v3_player_mouth_sequence(int index) {
    return (u32)index<130u ? native_mouth[index] : imported_face(index,1);
}
