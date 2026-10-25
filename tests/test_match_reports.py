import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from refresh_match_reports import discover

FIXTURE = dict(date='2026-10-24', opposition='Larkhall Athletic', homeAway='A', result='W 3-1')

def feed(description, url='https://www.tivertontownfc.uk/post/josh-does-the-biss-ness', published='Sun, 25 Oct 2026 12:23:45 GMT'):
    return f'<rss><channel><item><description>{description}</description><link>{url}</link><pubDate>{published}</pubDate></item></channel></rss>'

class ReportTests(unittest.TestCase):
    def test_away_report_requires_matching_score_and_date(self):
        description = 'Larkhall Athletic 1 Tiverton 3 | Report by Darren Holmes | Saturday October 24th'
        self.assertEqual(len(discover(feed(description), [FIXTURE])), 1)
        for wrong in ['Larkhall Athletic 3 Tiverton 1', 'Larkhall Athletic 1 Tiverton 4']:
            self.assertFalse(discover(feed(description.replace('Larkhall Athletic 1 Tiverton 3', wrong)), [FIXTURE]))
        self.assertFalse(discover(feed(description.replace('24th', '17th')), [FIXTURE]))

    def test_preview_old_match_unsafe_url_and_ambiguity_rejected(self):
        description = 'Larkhall Athletic 1 Tiverton 3 | Report by Darren Holmes | Saturday October 24th'
        self.assertFalse(discover(feed(description.replace('Report by', 'Match Preview by')), [FIXTURE]))
        self.assertFalse(discover(feed(description, published='Sun, 15 Nov 2026 12:23:45 GMT'), [FIXTURE]))
        self.assertFalse(discover(feed(description, url='https://example.com/post/fake'), [FIXTURE]))
        self.assertFalse(discover(feed(description), [FIXTURE, dict(FIXTURE)]))

    def test_home_report(self):
        fixture = dict(date='2026-10-17', opposition='PORTLAND UNITED', homeAway='H', result='L 1-4')
        self.assertEqual(len(discover(feed('Tiverton Town 1 Portland United 4 | Report by Darren Holmes | Saturday October 17th', published='Sun, 18 Oct 2026 12:23:45 GMT'), [fixture])), 1)

if __name__ == '__main__':
    unittest.main()
