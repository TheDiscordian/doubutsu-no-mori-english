#ifndef AF_CREATOR_ITEM_ARTICLE_H
#define AF_CREATOR_ITEM_ARTICLE_H

#define AF_ITEM_ARTICLE_BYTES 8576u

/* Receives the original native item ID and its full padded English name.
 * Returns the explicitly approved article 0..4, or -1 on failure. No writes.
 * The same native conversion used by af_load_item_name selects the record.
 */
int af_notice_item_article(unsigned int, const unsigned char *);

#endif
