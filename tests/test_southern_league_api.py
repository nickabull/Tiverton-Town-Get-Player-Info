"""Offline regression tests: no external API access required."""
import unittest
from southern_league_api import (
    canonical, extract_match, full_time, get_score, make_player_details,
)


class SouthernLeagueTests(unittest.TestCase):
    def fixture(self):
        return {
            "_id": "fixture-123",
            "date": "2026-11-07",
            "homeTeam": {"fullName": "Tiverton Town"},
            "awayTeam": {"fullName": "Sporting Club Inkberrow"},
            "score": {"current": {"home": 1, "away": 2}},
            "status": "FullTime",
            "homeLineup": [{"personName": "Player " + str(i), "number": i} for i in range(1, 12)],
            "homeBench": [{"personName": "Player 12", "number": 12}],
            "homeSubs": [{"minute": 53, "personOffName": "Player 11", "personOnName": "Player 12"}],
            "homeCards": [{"minute": 48, "personName": "Player 3", "cardType": "red_card"}],
            "homeGoals": [{"minute": 59, "personName": "Player 5"}],
        }

    def test_extract_tiverton_events(self):
        record = extract_match(self.fixture())
        self.assertEqual(record["date"], "2026-11-07")
        self.assertEqual(record["venue"], "H")
        self.assertEqual(record["score"], (1, 2))
        self.assertEqual(len(record["subs"]), 1)

    def test_match_details(self):
        record = extract_match(self.fixture())
        starters, bench = make_player_details(record)
        self.assertEqual(starters[10]["offMinute"], "53")
        self.assertTrue(bench[0]["used"])
        self.assertEqual(bench[0]["onMinute"], "53")
        self.assertEqual(starters[2]["cards"][0]["type"], "red_card")
        self.assertEqual(starters[4]["goalMinutes"], ["59"])

    def test_missing_starting_xi_never_inferred(self):
        row = self.fixture()
        del row["homeLineup"]
        self.assertIsNone(make_player_details(extract_match(row)))

    def test_away_team(self):
        row = self.fixture()
        row["awayTeam"], row["homeTeam"] = row["homeTeam"], row["awayTeam"]
        record = extract_match(row)
        self.assertEqual(record["venue"], "A")
        self.assertEqual(record["opponent"], "Sporting Club Inkberrow")

    def test_status(self):
        row = self.fixture()
        self.assertTrue(full_time(row))
        row["status"] = "InProgress"
        self.assertFalse(full_time(row))

    def test_name_suffix(self):
        self.assertEqual(canonical("Weymouth FC"), canonical("Weymouth"))
        self.assertEqual(get_score(self.fixture()), (1, 2))


if __name__ == "__main__":
    unittest.main()
