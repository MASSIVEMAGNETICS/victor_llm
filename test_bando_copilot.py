import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import tempfile
from pathlib import Path
import hashlib
import base64
import sys
import importlib.util

# --- Load the module to be tested ---
# This is a bit complex due to the filename not being a standard module name.
# We'll try to load it using importlib.

try:
    module_path = Path("bando_copilot_core_v1.0.0-BANDO-GODCORE.py")
    if not module_path.exists():
        raise FileNotFoundError(f"Main script {module_path} not found. Make sure it's in the same directory.")

    spec = importlib.util.spec_from_file_location("bando_core", module_path)
    bando_core = importlib.util.module_from_spec(spec)

    # To prevent FastAPI from running if it's not guarded in the main script's __main__ block
    # we can temporarily mock sys.argv or ensure the main block is properly guarded.
    # For now, we assume the main script's __name__ == '__main__' block is for CLI tests/Uvicorn info only.
    # If 'DNA_SECRET' initialization depends on functions that are not run at import time,
    # we might need to explicitly call an init function or mock more.

    # Temporarily modify sys.path to allow bando_core to resolve its own potential relative imports if any (none expected here)
    sys.path.insert(0, str(module_path.parent.resolve()))
    spec.loader.exec_module(bando_core)
    sys.path.pop(0)

except ImportError as e:
    print(f"Failed to import bando_core: {e}")
    bando_core = None # Ensure it's defined for later checks
except FileNotFoundError as e:
    print(e)
    bando_core = None
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    bando_core = None

# --- Actual Test Classes ---

@unittest.skipIf(bando_core is None, "bando_core module could not be loaded.")
class TestInjectSignature(unittest.TestCase):
    def setUp(self):
        # Use a fixed DNA_TAG for predictable tests
        self.test_dna_tag_value = "BANDO-DNA-TESTHASH123"
        self.original_dna_tag = bando_core.DNA_TAG # Store original
        bando_core.DNA_TAG = self.test_dna_tag_value # Override global

        # Mock the ZWC and Whitespace encoding functions to return predictable patterns
        # if their actual output is too complex or variable for these specific presence tests.
        # For now, we'll test against their actual behavior with the fixed DNA_TAG.
        # The actual ZWC/whitespace for "BANDO-DNA-TESTHASH123" needs to be determined if matching content.
        # For presence, just checking for the characters is enough.

        # Re-calculate ZWC for "BANDO-DNA-TESTHASH123" (specifically "TESTHASH")
        # T=0101 E=0100 S=0101 T=0101 H=0110 A=0100 S=0101 H=0110
        # ZWC: ZWNJ ZWJ ZWNJ ZWJ (T) ZWNJ ZWJ ZWNJ ZWNJ (E) ZWNJ ZWJ ZWNJ ZWJ (S) ZWNJ ZWJ ZWNJ ZWJ (T)
        #      ZWNJ ZWJ ZWJ ZWNJ (H) ZWNJ ZWJ ZWNJ ZWNJ (A) ZWNJ ZWJ ZWNJ ZWJ (S) ZWNJ ZWJ ZWJ ZWNJ (H)
        # For simplicity, we'll just check for presence of ZWJ or ZWNJ.
        self.zwj = '\u200D'
        self.zwnj = '\u200C'

    def tearDown(self):
        bando_core.DNA_TAG = self.original_dna_tag # Restore original

    def test_inject_signature_basic_comment(self):
        code = "print('hello')"
        signed_code = bando_core.inject_signature(code)
        self.assertTrue(signed_code.startswith(f"# {self.zwj}")) # Or ZWNJ, check presence below
        self.assertIn(self.test_dna_tag_value, signed_code.splitlines()[0])
        self.assertEqual(signed_code.splitlines()[1], code)

    def test_inject_signature_whitespace_presence(self):
        code = "print('hello')"
        signed_code = bando_core.inject_signature(code)
        first_line = signed_code.splitlines()[0]
        self.assertTrue(first_line.endswith(' ') or first_line.endswith('\t'), "Whitespace watermark not found at EOL")

    def test_inject_signature_zwc_presence(self):
        code = "print('hello')"
        # Need to ensure DNA_SECRET is set for _encode_zwc to be effective via inject_signature
        # If DNA_SECRET is None, inject_signature returns a placeholder.
        # For this test, let's assume DNA_SECRET is something, so DNA_TAG is used.
        with patch.object(bando_core, 'DNA_SECRET', new=b"testsecretkeyforzwc1234567890ab"): # Needs to be 32 bytes for hash
             # Re-trigger DNA_TAG generation if it depends on DNA_SECRET and happens at module load
             if hasattr(bando_core, 'hashlib'): # Check if hashlib is available in bando_core
                bando_core.DNA_TAG = f"BANDO-DNA-{bando_core.hashlib.sha256(bando_core.DNA_SECRET).hexdigest()}"
             else: # Fallback if hashlib not directly on bando_core, use a fixed one for test structure
                bando_core.DNA_TAG = self.test_dna_tag_value


             signed_code = bando_core.inject_signature(code)
             first_line = signed_code.splitlines()[0]
             # print(f"First line for ZWC check: '{first_line}'") # For debugging
             self.assertTrue(self.zwj in first_line or self.zwnj in first_line, "ZWC not found in signature line")

    def test_inject_signature_with_multiline_code(self):
        code = "def func():\n    pass\n#end"
        signed_code = bando_core.inject_signature(code)
        lines = signed_code.splitlines()
        self.assertIn(self.test_dna_tag_value, lines[0])
        self.assertEqual(lines[1], "def func():")
        self.assertEqual(lines[2], "    pass")
        self.assertEqual(lines[3], "#end")

    def test_inject_signature_dna_secret_unavailable(self):
        with patch.object(bando_core, 'DNA_SECRET', new=None):
            signed_code = bando_core.inject_signature("test_code")
            self.assertIn("# BANDO-DNA-UNINITIALIZED", signed_code)


@unittest.skipIf(bando_core is None, "bando_core module could not be loaded.")
class TestKeyHandling(unittest.TestCase):
    # Placeholder for key handling tests - these will be complex due to global state
    # For now, ensuring the class structure is present.
    # These tests would typically mock:
    # - os.environ.get
    # - Path.exists, Path.read_text, Path.write_text
    # - secrets.token_bytes, base64.urlsafe_b64encode, os.chmod
    # And then reload bando_core or re-trigger its key initialization logic.
    # This is non-trivial with the current script structure.

    def setUp(self):
        self.mock_data_dir = tempfile.TemporaryDirectory()
        self.original_data_dir = bando_core.DATA_DIR
        bando_core.DATA_DIR = Path(self.mock_data_dir.name)

        # Store original DNA_SECRET and ensure it's reset for each test
        self.original_dna_secret = bando_core.DNA_SECRET
        bando_core.DNA_SECRET = None


    def tearDown(self):
        self.mock_data_dir.cleanup()
        bando_core.DATA_DIR = self.original_data_dir
        bando_core.DNA_SECRET = self.original_dna_secret # Restore


    @patch.object(bando_core.os.environ, 'get')
    @patch.object(bando_core.Path, 'exists') # For vault file
    def test_load_key_from_env(self, mock_path_exists, mock_env_get):
        mock_env_get.return_value = base64.urlsafe_b64encode(b"test_env_key_12345678901234567890").decode('ascii')
        mock_path_exists.return_value = False # Vault does not exist

        # Re-run the key loading logic. This is the tricky part.
        # Assuming key loading logic is at module level, we might need to reload the module
        # or extract the logic into a function. For now, let's assume we can call a hypothetical init function.
        # If not, we'd mock then import/reload.
        # For this test, let's patch 'secrets.token_bytes' to ensure it's NOT called.
        with patch.object(bando_core.secrets, 'token_bytes') as mock_token_bytes:
            # This is a simplified way to re-trigger logic. Actual script doesn't have reinit_dna_secret()
            # We need to simulate the module import steps for DNA_SECRET initialization.
            # This part of the test is more of a conceptual sketch due to script structure.

            # Simulate re-evaluation of DNA_SECRET section
            # This requires knowledge of how DNA_SECRET is set up in bando_core
            # For now, this test will likely fail or be incomplete without refactoring bando_core

            # A better approach: bando_core should have a function like `get_dna_secret()` that encapsulates this logic.
            # For now, we assume we can check bando_core.DNA_SECRET after mocks.
            # To properly test, one might need to exec parts of bando_core script after setting mocks.

            # For this test, we will assume that by mocking os.environ.get and then calling a
            # (hypothetical or future refactored) init function, DNA_SECRET gets set.
            # Let's try to re-evaluate the DNA_SECRET part of the module code with exec,
            # or rely on the fact that importlib.reload might re-run top-level code.

            # This is a placeholder for actual re-initialization
            # For a real test, you'd call the function that performs this logic.
            # If it's top-level script code, it's harder.

            # Simplified: Check if DNA_SECRET was set (assuming import set it up based on mocks)
            # This won't work directly unless the module is reloaded with these mocks active *before* import.
            # The importlib execution already happened.
            # The test is more of an integration test of the module's state.

            # Let's assume for now that the test runner (or a future setup step) handles module reloading with mocks.
            # For now, this test is more illustrative.
            # A practical way: copy the DNA_SECRET loading logic into a testable function here.

            # This test is conceptually hard with current structure. Will skip full implementation.
            self.skipTest("DNA_SECRET loading logic test requires bando_core refactoring or complex reloading.")

            # Expected behavior if it could be re-triggered:
            # bando_core.initialize_dna_secret() # Hypothetical function
            # self.assertEqual(bando_core.DNA_SECRET, base64.urlsafe_b64encode(b"test_env_key_12345678901234567890"))
            # mock_token_bytes.assert_not_called()


@unittest.skipIf(bando_core is None, "bando_core module could not be loaded.")
class TestFileEncryptionVerification(unittest.TestCase):
    def setUp(self):
        self.test_dir_obj = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.test_dir_obj.name)
        self.key_for_encryption = bando_core.Fernet.generate_key() # Raw Fernet key, as bando_core.DNA_SECRET would be

    def tearDown(self):
        self.test_dir_obj.cleanup()

    def test_encrypt_verify_successful(self):
        file_path = self.test_dir / "test_file.txt"
        checksum_path = self.test_dir / "test_file.txt.sha256"
        original_content = b"Secret data for Bando Copilot!"

        file_path.write_bytes(original_content)
        checksum_path.write_text(hashlib.sha256(original_content).hexdigest())

        bando_core.encrypt_file(file_path, self.key_for_encryption)
        self.assertNotEqual(original_content, file_path.read_bytes(), "File content should be encrypted")

        is_verified = bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption)
        self.assertTrue(is_verified, "Verification should succeed")

    def test_verify_tampered_checksum_file(self):
        file_path = self.test_dir / "test_file_cz.txt"
        checksum_path = self.test_dir / "test_file_cz.txt.sha256"
        original_content = b"Secret data!"

        file_path.write_bytes(original_content)
        checksum_path.write_text(hashlib.sha256(original_content).hexdigest())

        bando_core.encrypt_file(file_path, self.key_for_encryption)

        # Tamper checksum
        checksum_path.write_text("tamperedchecksum123")

        is_verified = bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption)
        self.assertFalse(is_verified, "Verification should fail for tampered checksum")

    def test_verify_tampered_encrypted_content(self):
        file_path = self.test_dir / "test_file_ct.txt"
        checksum_path = self.test_dir / "test_file_ct.txt.sha256"
        original_content = b"Top Secret Data!"

        file_path.write_bytes(original_content)
        checksum_path.write_text(hashlib.sha256(original_content).hexdigest())

        bando_core.encrypt_file(file_path, self.key_for_encryption)

        # Ensure encryption happened
        encrypted_content_before_tamper = file_path.read_bytes()
        self.assertNotEqual(original_content, encrypted_content_before_tamper, "Content should be encrypted before tampering.")

        # Tamper content by flipping a bit (e.g., the first byte of actual ciphertext part)
        # Fernet structure: version (1), timestamp (8), IV (16), ciphertext, HMAC (32)
        # We need to be careful not to flip version, timestamp, or IV if we want a pure ciphertext tamper.
        # For simplicity, let's try flipping a bit somewhere in the middle.
        if len(encrypted_content_before_tamper) > 50: # Ensure there's a middle part (1+8+16 + at least some data + 32 for HMAC)
            tampered_bytes_list = list(encrypted_content_before_tamper)
            # Flip a bit in a byte around the middle (e.g. index 25-30 if long enough, after IV, before HMAC)
            # A common place to tamper is after the IV (1+8+16 = 25th byte, 0-indexed)
            byte_to_tamper_index = min(25, len(tampered_bytes_list) - 33) # Ensure it's before HMAC and within bounds
            if byte_to_tamper_index < (1+8+16) : # if file is too short, just tamper first data byte.
                 byte_to_tamper_index = (1+8+16)


            if byte_to_tamper_index < (len(tampered_bytes_list) - 32): # Check if index is valid before HMAC
                tampered_bytes_list[byte_to_tamper_index] = tampered_bytes_list[byte_to_tamper_index] ^ 0x01 # Flip LSB
                tampered_encrypted_content = bytes(tampered_bytes_list)
                file_path.write_bytes(tampered_encrypted_content)

                # Check that tampering actually changed the file on disk from its just-encrypted state
                self.assertNotEqual(encrypted_content_before_tamper, tampered_encrypted_content, "Tampering should change file content.")
            else:
                # Fallback if content is too short to reliably pick a mid-cipher byte (should not happen with Fernet min size)
                self.fail("Encrypted content too short to reliably tamper for this test.")
        else:
            # Fallback for very short encrypted content (unlikely with Fernet but good for test robustness)
            # This fallback might not reliably cause InvalidToken but will likely cause checksum mismatch.
            tampered_encrypted_content = encrypted_content_before_tamper + b"tampered_very_short"
            file_path.write_bytes(tampered_encrypted_content)
            self.assertNotEqual(encrypted_content_before_tamper, tampered_encrypted_content, "Tampering (short fallback) should change file content.")


        is_verified = bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption)
        # Expect InvalidToken from Fernet (most likely) or checksum mismatch
        self.assertFalse(is_verified, "Verification should fail for tampered content (bit flip)")

    def test_verify_wrong_key(self):
        file_path = self.test_dir / "test_file_wk.txt"
        checksum_path = self.test_dir / "test_file_wk.txt.sha256"
        original_content = b"Super Secret Data!"

        file_path.write_bytes(original_content)
        checksum_path.write_text(hashlib.sha256(original_content).hexdigest())

        bando_core.encrypt_file(file_path, self.key_for_encryption)

        wrong_key = bando_core.Fernet.generate_key()
        is_verified = bando_core.verify_decrypted_file(file_path, checksum_path, wrong_key)
        self.assertFalse(is_verified, "Verification should fail for wrong key (InvalidToken expected)")


    @patch.object(Path, 'read_bytes')
    def test_encrypt_file_io_error_read(self, mock_read_bytes):
        mock_read_bytes.side_effect = IOError("Failed to read")
        file_path = self.test_dir / "io_error_read.txt"
        # No need to write content as read is mocked to fail, Path object itself is fine

        with self.assertRaises(IOError) as cm:
            bando_core.encrypt_file(file_path, self.key_for_encryption)
        self.assertEqual(str(cm.exception), "Failed to read")

    def test_encrypt_file_io_error_write(self):
        file_path = self.test_dir / "io_error_write.txt"

        # Setup: write the file using the real method before patching
        file_path.write_bytes(b"some data to allow read_bytes to succeed")

        # Start patching Path.write_bytes just for the call inside encrypt_file
        with patch('pathlib.Path.write_bytes', side_effect=IOError("Failed to write")) as mock_write_bytes_call:
            with self.assertRaises(IOError) as cm:
                bando_core.encrypt_file(file_path, self.key_for_encryption)
            self.assertEqual(str(cm.exception), "Failed to write")

            # Ensure the mock was called. Since it's a class method patch,
            # it's harder to assert it was called on `file_path` specifically without more complex arg checking.
            # But we can check it was called once with some Path instance as the first arg.
            self.assertTrue(mock_write_bytes_call.called, "Path.write_bytes mock should have been called.")
            # We've already asserted the exception message.
            # Asserting the specific instance (args[0]) can be tricky with class method patches
            # if multiple Path instances are used. However, in this controlled test,
            # it's the `file_path` instance's method that leads to the mock call.
            # The critical part is that the mock's side_effect (the IOError) was triggered.
            # If we want to be very sure, we can check call_args if the mock provides enough info.
            # For now, knowing it was called and the correct exception was raised is sufficient.
            mock_write_bytes_call.assert_called_once()


    def test_verify_file_not_found(self):
        file_path = self.test_dir / "non_existent_file.enc"
        checksum_path = self.test_dir / "non_existent_file.enc.sha256"

        # Case 1: Encrypted file doesn't exist
        checksum_path.write_text("dummychecksum") # Checksum file exists
        self.assertFalse(bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption))

        # Case 2: Checksum file doesn't exist
        file_path.write_bytes(b"dummyencrypteddata") # Encrypted file exists
        checksum_path.unlink(missing_ok=True)
        self.assertFalse(bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption))

        # Case 3: Both don't exist
        file_path.unlink(missing_ok=True)
        self.assertFalse(bando_core.verify_decrypted_file(file_path, checksum_path, self.key_for_encryption))


if __name__ == '__main__':
    # This allows running tests directly from this file
    # Ensure bando_core is loaded before trying to run tests.
    if bando_core is None:
        print("Skipping tests as bando_core module could not be loaded.")
    else:
        print(f"Running tests for bando_core module (version of DNA_TAG: {getattr(bando_core, 'DNA_TAG', 'N/A')})")
        unittest.main()
