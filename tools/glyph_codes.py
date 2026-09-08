"""Explicit dialogue-only encodings for the separate source-verified font."""

ENCODINGS = {';': b'\x80\xd0', '/': b'\x80\xae', '☀': b'\x80\xa7',
             '☃': b'\x80\xab', '💀': b'\x80\xba'}
WIDTHS = {ENCODINGS[c]: width for c, width in ((';', 3), ('/', 6), ('☀', 12),
                                            ('☃', 12), ('💀', 12))}
