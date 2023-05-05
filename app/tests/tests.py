import unittest
from databases import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database("sqlite:///./test.db")

    def test_connect(self):
        self.assertIsNotNone(self.db.connect())

    async def test_execute(self):
        query = "SELECT * FROM predictions"
        result = await self.db.fetch_one(query=query)
        await self.assertIsInstance(result, list)
        await self.assertGreater(len(result), 0)

    def tearDown(self):
        self.db.disconnect()
