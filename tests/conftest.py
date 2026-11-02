"""
Shared pytest setup.

app.config.settings raises at import time when the OpenAI settings are
missing, and app.utils.data_loader loads data at import time. Dummy values
and CSV mode let the test suite import the app without real credentials or
a database. No test makes a real OpenAI call.
"""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "test-model")
os.environ["DATA_SOURCE"] = "csv"
