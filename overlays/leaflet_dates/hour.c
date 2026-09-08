/* Full English leaflet time; callers own at least seven temporary bytes.
 * This is separate from the numeric-only main-dialogue hour insertion.
 */
int af_leaflet_hour(unsigned char *out, unsigned int hour) {
    unsigned int value, length = 0;
    if (!out) return -1;
    if (hour > 23u) hour = 0;
    value = hour < 12u ? hour : hour-12u;
    if (!value) value = 12u;
    if (value >= 10u) {
        out[length++] = '1';
        value -= 10u;
    }
    out[length++] = (unsigned char)('0'+value);
    out[length++] = ' ';
    out[length++] = hour < 12u ? 'a' : 'p';
    out[length++] = '.';
    out[length++] = 'm';
    out[length++] = '.';
    /* Only the returned length is passed to the native free-string setter. */
    return (int)length;
}
