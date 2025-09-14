import unittest
import asyncio
import io
import discord
from utils.crypto import is_long_text, create_text_file, base64_encode, base64_decode

class TestCryptoLongText(unittest.TestCase):
    def test_is_long_text(self):
        """Test long text detection"""
        short_text = "Hello World"
        long_text = "A" * 2000

        self.assertFalse(is_long_text(short_text))
        self.assertTrue(is_long_text(long_text))

    def test_is_long_text_boundary(self):
        """Test boundary conditions"""
        boundary_short = "A" * 1500
        boundary_long = "A" * 1501

        self.assertFalse(is_long_text(boundary_short))
        self.assertTrue(is_long_text(boundary_long))

    def test_create_text_file(self):
        """Test text file creation"""
        async def run_test():
            content = "Hello\nWorld\n"
            filename = "test.txt"

            file = await create_text_file(content, filename)

            self.assertIsInstance(file, discord.File)
            self.assertEqual(file.filename, filename)

            # Read content back
            file.fp.seek(0)
            read_content = file.fp.read()
            self.assertEqual(read_content, content)

        asyncio.run(run_test())

    def test_crypto_with_long_text(self):
        """Test crypto functions with long text"""
        short_text = "Hello World"
        long_text = "A" * 2000

        # Test base64 encoding/decoding with long text
        encoded_short = base64_encode(short_text)
        decoded_short = base64_decode(encoded_short)
        self.assertEqual(decoded_short, short_text)

        encoded_long = base64_encode(long_text)
        decoded_long = base64_decode(encoded_long)
        self.assertEqual(decoded_long, long_text)

        # Verify that encoded long text is also long
        self.assertTrue(is_long_text(encoded_long))

    def test_long_text_threshold(self):
        """Test that the threshold is appropriate for Discord embeds"""
        # Discord embeds have a 2048 character limit for description
        # Our threshold of 1500 should be safe
        test_text = "A" * 1500
        self.assertFalse(is_long_text(test_text))

        # But 1501 should trigger file mode
        test_text_long = "A" * 1501
        self.assertTrue(is_long_text(test_text_long))

if __name__ == '__main__':
    unittest.main()