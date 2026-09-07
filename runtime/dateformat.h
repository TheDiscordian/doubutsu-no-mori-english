#ifndef AF_DATEFORMAT_H
#define AF_DATEFORMAT_H

enum AfDatePart {
    AF_YEAR, AF_MONTH, AF_WEEKDAY, AF_DAY, AF_HOUR, AF_MINUTE, AF_SECOND,
    AF_AMPM
};

/* Returns the unpadded length, or -1 without writing if capacity is insufficient. */
int af_date_format(unsigned char *out, unsigned capacity, unsigned part, unsigned value);
int af_format_year(unsigned char *out, unsigned value);
int af_format_month(unsigned char *out, unsigned value);
int af_format_weekday(unsigned char *out, unsigned value);
int af_format_day(unsigned char *out, unsigned value);
int af_format_hour(unsigned char *out, unsigned value);
int af_format_minute(unsigned char *out, unsigned value);
int af_format_second(unsigned char *out, unsigned value);
extern const unsigned char af_leap_month[10];

#endif
