import unittest

from dataGenerator.build_body_metrics import parse_height_cm


class ParseHeightCmTests(unittest.TestCase):
    def test_accepts_integer_height_values(self) -> None:
        self.assertEqual(parse_height_cm(150), 150)

    def test_accepts_string_height_values(self) -> None:
        self.assertEqual(parse_height_cm("150cm"), 150)


if __name__ == "__main__":
    unittest.main()
