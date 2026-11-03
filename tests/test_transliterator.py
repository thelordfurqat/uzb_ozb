import unittest
from transliterator import convert

class TransliterationTests(unittest.TestCase):
    def test_cyr_to_new(self):
        self.assertEqual(convert("Ўзбекистон", "cyr"), "Özbekiston")

    def test_old_to_new(self):
        self.assertEqual(convert("O‘zbekiston", "old"), "Özbekiston")

    def test_new_to_old(self):
        self.assertEqual(convert("Özbekiston", "newToOld"), "O‘zbekiston")

    def test_new_to_cyr(self):
        self.assertEqual(convert("Özbekiston", "newToCyr"), "Ўзбекистон")

    def test_case(self):
        self.assertEqual(convert("ЯНГИ", "cyr"), "YANGI")
        self.assertEqual(convert("Янги", "cyr"), "Yangi")

    def test_punctuation(self):
        self.assertEqual(convert("Салом, дунё!", "cyr"), "Salom, dunyo!")

if __name__ == "__main__":
    unittest.main()
