"""Complete native design grammar retains all IDs and full name CRC checks."""

import unittest
import test_item_articles as legacy
from item_articles import DESIGN_NAMES_HASH, DESIGN_DATA_HASH


@unittest.skipUnless((legacy.ROOT/'build/design-items-articles/articles.bin').is_file(), 'Local native-design articles required')
class DesignItemArticleTests(legacy.ItemArticleTests):
    directory = legacy.ROOT/'build/design-items-articles'
    names_directory = legacy.ROOT/'build/design-items-resource'
    data_hash, names_hash, known_slots = DESIGN_DATA_HASH, DESIGN_NAMES_HASH, 4536


if __name__ == '__main__': unittest.main()
