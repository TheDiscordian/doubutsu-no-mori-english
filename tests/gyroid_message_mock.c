int af_gyroid_widths[256];
unsigned int af_gyroid_width_calls;
int af_gyroid_test_width(unsigned char code) {
    ++af_gyroid_width_calls;
    return af_gyroid_widths[code];
}
