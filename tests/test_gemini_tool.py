import os
import unittest
from unittest.mock import patch

from tools.gemini_tool import GeminiToolError, generate_structured_json


class GeminiToolTransportTest(unittest.TestCase):
    def test_generate_structured_json_wraps_timeout_as_gemini_tool_error(self) -> None:
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False),
            patch("tools.gemini_tool.urlopen", side_effect=TimeoutError),
        ):
            with self.assertRaises(GeminiToolError) as context:
                generate_structured_json(
                    prompt="translate this",
                    schema={
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                )

        self.assertIn("timeout", str(context.exception).lower())
