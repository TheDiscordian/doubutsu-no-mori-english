"""Native DMA batches select exact messages without changing review metadata."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from message_alias_test_scenario import select_messages


class DialogueBatchTests(unittest.TestCase):
    def test_explicit_batch_includes_candidates_and_drafts(self):
        edits = [{"id": "message:0001", "status": "draft"},
                 {"id": "message:0002", "status": "mechanically_validated_candidate_not_reviewed"},
                 {"id": "message:0003", "status": "draft"}]
        self.assertEqual(select_messages(edits, message_ids=["message:0001", "message:0002"]), edits[:2])
        self.assertEqual(select_messages(edits, drafts=True), [edits[0], edits[2]])
        for ids in ([], ["message:0001"]*2, ["message:0004"]):
            with self.assertRaises(ValueError):
                select_messages(edits, message_ids=ids)
        with self.assertRaises(ValueError):
            select_messages(edits, drafts=True, message_ids=["message:0001"])
        with self.assertRaises(ValueError):
            select_messages([edits[0]]*2, message_ids=["message:0001"])
        with self.assertRaises(ValueError):
            select_messages([{"id": "select:0001"}], message_ids=["select:0001"])


if __name__ == "__main__":
    unittest.main()
