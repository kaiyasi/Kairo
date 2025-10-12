import unittest
import sqlite3
import os
import tempfile
from ..utils.tenant import tenant_db

class TestChannelRouting(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp()
        # Temporarily override the database path
        tenant_db.db_path = self.test_db_path
        tenant_db.init_db()

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_set_and_get_channel_routing(self):
        """Test setting and getting channel routing"""
        guild_id = 12345
        key = "plan_status"
        channel_id = 67890

        # Set routing
        with sqlite3.connect(self.test_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO routing (guild_id, key, channel_id)
                VALUES (?, ?, ?)
            """, (guild_id, key, channel_id))

        # Get routing
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute(
                "SELECT channel_id FROM routing WHERE guild_id = ? AND key = ?",
                (guild_id, key)
            )
            row = cursor.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], channel_id)

    def test_get_nonexistent_routing(self):
        """Test getting non-existent routing returns None"""
        guild_id = 12345
        key = "nonexistent"

        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute(
                "SELECT channel_id FROM routing WHERE guild_id = ? AND key = ?",
                (guild_id, key)
            )
            row = cursor.fetchone()

        self.assertIsNone(row)

    def test_multiple_routings_per_guild(self):
        """Test multiple routings for same guild"""
        guild_id = 12345
        routings = [
            ("plan_status", 11111),
            ("attendance_summary", 22222),
            ("ctf_notice", 33333)
        ]

        # Set multiple routings
        with sqlite3.connect(self.test_db_path) as conn:
            for key, channel_id in routings:
                conn.execute("""
                    INSERT OR REPLACE INTO routing (guild_id, key, channel_id)
                    VALUES (?, ?, ?)
                """, (guild_id, key, channel_id))

        # Get all routings for guild
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute(
                "SELECT key, channel_id FROM routing WHERE guild_id = ?",
                (guild_id,)
            )
            rows = cursor.fetchall()

        self.assertEqual(len(rows), 3)
        result_dict = dict(rows)

        for key, expected_channel_id in routings:
            self.assertIn(key, result_dict)
            self.assertEqual(result_dict[key], expected_channel_id)

if __name__ == '__main__':
    unittest.main()