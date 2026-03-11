import unittest

from backend.site_data import filter_summaries


class FilterSummariesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = {
            "summaries": [
                {
                    "slug": "teio",
                    "name_zh": "东海帝王",
                    "theme_group": "主角气场",
                    "personality_tags": ["元气感", "挑战者"],
                    "counts": {"support_cards": 10, "character_cards": 3, "relations": 6},
                    "metrics": {"height_cm": 150, "bust_cm": 77},
                    "filters": {
                        "birthday_month": 4,
                        "distance_tags": ["middle", "long"],
                        "style_tags": ["leader"],
                        "support_command_tags": ["速度", "力量"],
                        "limited": False,
                    },
                    "search_blob": "东海帝王 tokuai teio leader middle",
                    "latest_outfit_at_ts": 1700000000,
                },
                {
                    "slug": "mcqueen",
                    "name_zh": "目白麦昆",
                    "theme_group": "名门优雅",
                    "personality_tags": ["名门气质"],
                    "counts": {"support_cards": 2, "character_cards": 1, "relations": 1},
                    "metrics": {"height_cm": 159, "bust_cm": 71},
                    "filters": {
                        "birthday_month": 4,
                        "distance_tags": ["long"],
                        "style_tags": ["leader"],
                        "support_command_tags": ["耐力"],
                        "limited": True,
                    },
                    "search_blob": "目白麦昆 mejiro mcqueen long leader",
                    "latest_outfit_at_ts": 1600000000,
                },
            ]
        }

    def test_filters_by_multiple_dimensions(self) -> None:
        items = filter_summaries(
            self.dataset,
            {
                "distance": "middle,long",
                "theme_group": "主角气场",
                "personality": "元气感",
                "support_command": "速度",
                "min_support_cards": "5",
                "query": "帝王",
            },
        )
        self.assertEqual([item["slug"] for item in items], ["teio"])

    def test_filters_limited_and_numeric_ranges(self) -> None:
        items = filter_summaries(
            self.dataset,
            {
                "limited": "1",
                "min_height": "155",
                "max_bust": "72",
            },
        )
        self.assertEqual([item["slug"] for item in items], ["mcqueen"])


if __name__ == "__main__":
    unittest.main()
