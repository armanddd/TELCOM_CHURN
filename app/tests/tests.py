import asyncio
import unittest
import requests
from databases import Database


class TestDatabaseAndPredictions(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.db = Database("sqlite:///./../test.db")

    def test_connect(self):
        async def connect():
            await self.db.connect()
            self.assertIsNotNone(self.db.connection)

        self.loop.run_until_complete(connect())

    async def table_exists(self, table_name):
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        result = await self.db.fetch_all(query=query)
        return len(result) > 0

    def test_execute(self):
        async def execute():
            await self.db.connect()

            # Check if the "predictions" table exists
            if not await self.table_exists("predictions"):
                raise AssertionError("Table 'predictions' does not exist")

            # Check if the "predictions" table exists
            if not await self.table_exists("requests"):
                raise AssertionError("Table 'requests' does not exist")

            # Check if the "predictions" table exists
            if not await self.table_exists("users"):
                raise AssertionError("Table 'users' does not exist")

            await self.db.disconnect()

        self.loop.run_until_complete(execute())

    def test_make_prediction(self):
        # test with form request
        form_data = {
            "tenureForm": 5,
            "genderSelect": "Male",
            "seniorCitizenSelect": 1,
            "partnerSelect": "Yes",
            "dependentsSelect": "No",
            "phoneServiceSelect": "No",
            "multipleLinesSelect": "No",
            "internetServiceSelect": "Yes",
            "onlineSecuritySelect": "Yes",
            "onlineBackupSelect": "Yes",
            "deviceProtectionSelect": "No",
            "techSupportSelect": "No",
            "streamingTVSelect": "No",
            "streamingMoviesSelect": "No",
            "contractTypeSelect": "One year",
            "paymentMethodSelect": "Credit card (automatic)",
            "paperlessBillingSelect": "Yes",
            "monthlyChargesForm": 25,
            "totalChargesForm": 125,
            "api_key": "aea68b2ed97163cd24fa146609fbcd31"
        }

        response = requests.post("http://localhost:8000/make_prediction", data=form_data)
        self.assertEqual(response.status_code, 200)
        form_text = response.text

        # test with file request
        with open("./../static/files/Churn Prediction Template.xlsx", "rb") as file:
            response = requests.post("http://localhost:8000/make_prediction", files={"templateFile": file},
                                     data={"api_key": "aea68b2ed97163cd24fa146609fbcd31"})
            self.assertEqual(response.status_code, 200)
            file_text = response.text

        # Define the expected starting strings
        expected_start_strings = ["{\"churn_prediction", "\"Your template with the predictions can be found at"]

        # Check if the response starts with any of the expected strings
        starts_with_expected_string_form = any(form_text.startswith(string) for string in expected_start_strings)
        starts_with_expected_string_file = any(file_text.startswith(string) for string in expected_start_strings)

        self.assertTrue(starts_with_expected_string_form,
                        f"Response does not start with any of the expected strings: {expected_start_strings}")

        self.assertTrue(starts_with_expected_string_file,
                        f"Response does not start with any of the expected strings: {expected_start_strings}")

    def tearDown(self):
        self.loop.run_until_complete(self.db.disconnect())
        self.loop.close()
        asyncio.set_event_loop(None)
