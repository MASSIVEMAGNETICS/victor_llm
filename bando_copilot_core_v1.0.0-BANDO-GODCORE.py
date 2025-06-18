import uuid
import os
import secrets
import hashlib
import logging
from pathlib import Path
import time
import tempfile
import base64

# Third-party imports
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    # This is a critical dependency. Log and exit or raise if not found.
    # For now, we'll let it fail at runtime if 'pip install cryptography' wasn't done.
    logging.critical("Cryptography library not found. Please install it: pip install cryptography")
    # raise # Or sys.exit(1)

try:
    from fastapi import FastAPI, HTTPException, Body, Response
    from pydantic import BaseModel
except ImportError:
    logging.critical("FastAPI or Pydantic library not found. Please install them: pip install fastapi pydantic uvicorn")
    # raise # Or sys.exit(1)


# --- LOGGING SETUP ---
LOG_LEVEL = os.environ.get("BANDO_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- DATA DIRECTORY ---
DATA_DIR = Path.home() / ".bando_copilot_data" # Changed name slightly to avoid conflict if old one exists
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log.info(f"Data directory ensured: {DATA_DIR}")
except OSError as e:
    log.error(f"Could not create data directory {DATA_DIR}: {e}. File operations may fail.")
    # Depending on the application, might exit or use a fallback.

# === CONFIG ===
ENV_VAR_DNA_SECRET = "BANDO_DNA_SECRET"
VAULT_FILE_PATH = DATA_DIR / ".dna_secret_vault"
DNA_SECRET = None # This will store the key as bytes, suitable for Fernet

# Attempt 1: Load from Environment Variable
try:
    env_key_str = os.environ.get(ENV_VAR_DNA_SECRET)
    if env_key_str:
        DNA_SECRET = env_key_str.encode('ascii') # Key is stored as base64 string, convert to bytes
        # Test if it's a valid Fernet key early
        Fernet(DNA_SECRET)
        log.info(f"Loaded and validated DNA_SECRET from environment variable {ENV_VAR_DNA_SECRET}")
except (ValueError, TypeError) as e: # Fernet() can raise ValueError on bad key, TypeError if not bytes
    log.warning(f"Failed to load/validate DNA_SECRET from ENV {ENV_VAR_DNA_SECRET}: {e}. Trying vault file.")
    DNA_SECRET = None
except Exception as e: # Catch any other unexpected errors
    log.warning(f"An unexpected error occurred while loading DNA_SECRET from ENV {ENV_VAR_DNA_SECRET}: {e}. Trying vault file.")
    DNA_SECRET = None


# Attempt 2: Load from Vault File (if not found in ENV)
if DNA_SECRET is None:
    if VAULT_FILE_PATH.exists():
        try:
            key_str = VAULT_FILE_PATH.read_text().strip()
            if key_str:
                DNA_SECRET = key_str.encode('ascii') # Key is stored as base64 string
                # Test if it's a valid Fernet key early
                Fernet(DNA_SECRET)
                log.info(f"Loaded and validated DNA_SECRET from vault file: {VAULT_FILE_PATH}")
            else:
                log.warning(f"Vault file {VAULT_FILE_PATH} is empty. Will generate a new key.")
        except (IOError, OSError) as e:
            log.warning(f"Could not read vault file {VAULT_FILE_PATH}: {e}")
            DNA_SECRET = None
        except (ValueError, TypeError) as e: # Fernet() can raise ValueError on bad key
            log.warning(f"Failed to load/validate DNA_SECRET from vault file {VAULT_FILE_PATH}: {e}")
            DNA_SECRET = None
        except Exception as e: # Catch any other unexpected errors
            log.warning(f"An unexpected error occurred while loading DNA_SECRET from vault {VAULT_FILE_PATH}: {e}")
            DNA_SECRET = None
    else:
        log.info(f"Vault file {VAULT_FILE_PATH} not found. Will generate a new key if needed.")

# Attempt 3: Generate New Key (if not found in ENV or Vault)
if DNA_SECRET is None:
    log.info("Generating new DNA_SECRET.")
    raw_key = secrets.token_bytes(32)
    DNA_SECRET = base64.urlsafe_b64encode(raw_key) # Generate a URL-safe base64 encoded key
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True) # Ensure DATA_DIR exists before writing
        VAULT_FILE_PATH.write_text(DNA_SECRET.decode('ascii')) # Store as base64 string
        log.info(f"Saved new DNA_SECRET (base64 encoded) to vault file: {VAULT_FILE_PATH}")
        try:
            os.chmod(VAULT_FILE_PATH, 0o600)
            log.info(f"Set permissions for {VAULT_FILE_PATH} to 600.")
        except OSError as e:
            log.warning(f"Could not set permissions for {VAULT_FILE_PATH}. Please restrict manually if possible. Error: {e}")
    except (IOError, OSError) as e:
        log.error(f"CRITICAL: Failed to save new DNA_SECRET to vault file {VAULT_FILE_PATH}: {e}")
    except Exception as e: # Catch any other unexpected errors
        log.error(f"CRITICAL: An unexpected error occurred while saving new DNA_SECRET to {VAULT_FILE_PATH}: {e}")


if DNA_SECRET is None:
    log.critical("DNA_SECRET could not be initialized. Encryption/decryption services will not work.")
    # Application might choose to exit or operate in a degraded mode.
    # For now, we'll allow it to continue, but endpoints requiring DNA_SECRET will fail.

# --- METADATA ---
DNA_TAG = "" # Initialize DNA_TAG
if DNA_SECRET: # Only generate DNA_TAG if DNA_SECRET is available
    DNA_TAG = f"BANDO-DNA-{hashlib.sha256(DNA_SECRET).hexdigest()}"
else:
    log.warning("DNA_SECRET not available. DNA_TAG will be a placeholder UUID.")
    DNA_TAG = f"BANDO-DNA-{uuid.uuid4().hex}" # Fallback if DNA_SECRET isn't set

# --- WATERMARKING ---
def _encode_whitespace(tag_to_encode: str) -> str:
    binary_tag = ''.join(format(ord(char), '08b') for char in tag_to_encode)
    return binary_tag.replace('1', '\t').replace('0', ' ')

def _encode_zwc(tag_to_encode: str) -> str:
    hash_part = tag_to_encode.split('-')[-1]
    hex_to_encode = ''.join(filter(lambda x: x in '0123456789abcdefABCDEF', hash_part))[:8]
    if not hex_to_encode: return ""
    binary_representation = "".join(format(int(hex_char, 16), '04b') for hex_char in hex_to_encode)
    return binary_representation.replace('1', '\u200D').replace('0', '\u200C')

def inject_signature(text: str) -> str:
    if not DNA_SECRET: # If DNA_SECRET isn't available, don't try to inject a hash-based signature
        log.warning("Cannot inject full signature as DNA_SECRET is not available.")
        return f"# BANDO-DNA-UNINITIALIZED\n{text}"
    whitespace_watermark = _encode_whitespace(DNA_TAG)
    zwc_watermark = _encode_zwc(DNA_TAG)
    return f"# {zwc_watermark}{DNA_TAG}{whitespace_watermark}\n{text}"


# --- FILE OPERATIONS ---
def encrypt_file(path: Path, key: bytes):
    """Encrypts a file using Fernet encryption."""
    if not key:
        log.error(f"Encryption key is missing. Cannot encrypt {path}.")
        raise ValueError("Encryption key is not available.")
    f = Fernet(key)
    try:
        original_data = path.read_bytes()
    except (IOError, OSError) as e:
        log.error(f"Error reading file {path} for encryption: {e}")
        raise # Re-raise the exception

    encrypted_data = f.encrypt(original_data)

    try:
        path.write_bytes(encrypted_data)
        log.info(f"File encrypted successfully: {path}")
    except (IOError, OSError) as e:
        log.error(f"Error writing encrypted file {path}: {e}")
        raise # Re-raise the exception

def decrypt_file_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Helper to decrypt data, used by verify_decrypted_file."""
    if not key:
        log.error(f"Decryption key is missing.")
        raise ValueError("Decryption key is not available.")
    f = Fernet(key)
    return f.decrypt(encrypted_data)


def verify_decrypted_file(encrypted_path: Path, checksum_path: Path, key: bytes) -> bool:
    """Verifies a decrypted file against its checksum."""
    if not key:
        log.error(f"Decryption key is missing. Cannot verify {encrypted_path}.")
        return False

    expected_checksum = ""
    encrypted_data = b""

    try:
        if not checksum_path.exists():
            log.error(f"Checksum file not found: {checksum_path}")
            return False
        expected_checksum = checksum_path.read_text().strip()
    except (IOError, OSError) as e:
        log.error(f"Error reading checksum file {checksum_path}: {e}")
        return False
    except Exception as e_verify: # Catch any other unexpected errors
        log.error(f"Unexpected error reading checksum {checksum_path}: {e_verify}")
        return False

    try:
        if not encrypted_path.exists():
            log.error(f"Encrypted file not found: {encrypted_path}")
            return False
        encrypted_data = encrypted_path.read_bytes()
    except (IOError, OSError) as e:
        log.error(f"Error reading encrypted file {encrypted_path}: {e}")
        return False
    except Exception as e_verify:
        log.error(f"Unexpected error reading encrypted file {encrypted_path}: {e_verify}")
        return False

    try:
        decrypted_data = decrypt_file_data(encrypted_data, key)
    except InvalidToken:
        log.error(f"Invalid token: Decryption failed for {encrypted_path}. The key may be wrong or data corrupted.")
        return False
    except ValueError as ve: # Catch key missing from decrypt_file_data
        log.error(f"Decryption error for {encrypted_path}: {ve}")
        return False
    except Exception as e_verify:
        log.error(f"Unexpected error during decryption of {encrypted_path}: {e_verify}")
        return False

    calculated_checksum = hashlib.sha256(decrypted_data).hexdigest()
    is_valid = calculated_checksum == expected_checksum

    log.info(f"Checksum verification for {encrypted_path}: {'SUCCESS' if is_valid else 'FAILURE'}")
    if not is_valid:
        log.warning(f"Expected checksum: {expected_checksum}, Calculated: {calculated_checksum}")
    return is_valid

# --- FastAPI APP ---
app = FastAPI()

class CodeInput(BaseModel):
    code: str

@app.post("/generate/")
async def generate_code_file(payload: CodeInput = Body(...)):
    if not DNA_SECRET:
        log.error("DNA_SECRET not initialized. Cannot process /generate request.")
        raise HTTPException(status_code=500, detail="Server secret not initialized. Cannot generate file.")

    code = payload.code
    final_file_path = DATA_DIR / f"gen_{int(time.time())}.py"
    checksum_file_path = DATA_DIR / (final_file_path.name + ".sha256")
    temp_file_path: Path | None = None # Ensure type hint for Path or None

    try:
        signed_code_str = inject_signature(code)
        signed_code_bytes = signed_code_str.encode('utf-8')

        # Write to Temp File
        # tempfile.NamedTemporaryFile needs delete=False to allow rename on some OS (Windows)
        with tempfile.NamedTemporaryFile(mode="wb", dir=DATA_DIR, delete=False) as tmp_file:
            tmp_file.write(signed_code_bytes)
            temp_file_path = Path(tmp_file.name)

        # Calculate and Save Checksum
        current_checksum = hashlib.sha256(signed_code_bytes).hexdigest()
        try:
            checksum_file_path.write_text(current_checksum, encoding="utf-8")
        except (IOError, OSError) as e_checksum:
            log.error(f"Failed to write checksum file {checksum_file_path}: {e_checksum}")
            # Attempt cleanup before re-raising or handling
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to write checksum file: {e_checksum}")

        # Atomic Rename
        temp_file_path.rename(final_file_path)
        log.info(f"Generated file saved: {final_file_path}")
        log.info(f"Checksum saved: {checksum_file_path}")
        temp_file_path = None # Mark as moved

        # Encrypt File
        encrypt_file(final_file_path, DNA_SECRET) # This will log and re-raise on failure

        return {"file": str(final_file_path), "signature_dna_tag": DNA_TAG, "checksum_file": str(checksum_file_path)}

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except (IOError, OSError, ValueError) as e_file_op: # Catch specific errors from encrypt_file or rename
        log.error(f"File operation error during /generate: {e_file_op}")
        # Cleanup temp files if they exist
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
        if checksum_file_path.exists(): # If checksum was written before rename failed
             # Check if final file exists, if not, then rename didn't happen, so checksum is for temp file
            if not final_file_path.exists():
                checksum_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"File operation error: {e_file_op}")
    except Exception as e_main:
        log.error(f"Failed to generate file: {e_main}", exc_info=True) # exc_info for traceback
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
        # If checksum was written but main operation failed (e.g. encryption), clean it up
        # only if the final file it corresponds to wasn't successfully created.
        if checksum_file_path.exists() and not final_file_path.exists():
             checksum_file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate file: {e_main}")


# --- Example Usage (CLI for testing some parts if not running FastAPI) ---
if __name__ == "__main__":
    log.info("Script started directly. DNA_SECRET/TAG initialization would have occurred.")
    log.info(f"Current DNA_TAG: {DNA_TAG}")
    log.info(f"Current DNA_SECRET (first few chars if available): {DNA_SECRET[:8].decode('ascii') + '...' if DNA_SECRET else 'Not set/Failed to init'}")

    if DNA_SECRET:
        # Test encryption and verification
        test_content = "print('Hello, Bando!')"
        test_file_base = f"test_encrypt_verify_{int(time.time())}"
        test_file = DATA_DIR / f"{test_file_base}.py"
        test_checksum_file = DATA_DIR / f"{test_file_base}.py.sha256"

        try:
            log.info(f"Creating test file: {test_file}")
            signed_test_content = inject_signature(test_content)
            test_file.write_text(signed_test_content)

            # Create checksum for original signed content
            original_checksum = hashlib.sha256(signed_test_content.encode('utf-8')).hexdigest()
            test_checksum_file.write_text(original_checksum)
            log.info(f"Test checksum saved: {test_checksum_file} ({original_checksum})")

            log.info(f"Encrypting {test_file}...")
            encrypt_file(test_file, DNA_SECRET)

            log.info(f"Verifying {test_file} against {test_checksum_file}...")
            is_verified = verify_decrypted_file(test_file, test_checksum_file, DNA_SECRET)
            log.info(f"Verification result for {test_file}: {is_verified}")

            # Clean up test files
            # test_file.unlink(missing_ok=True)
            # test_checksum_file.unlink(missing_ok=True)
            # log.info("Cleaned up test files.")

        except Exception as e:
            log.error(f"Error in __main__ test block: {e}", exc_info=True)
    else:
        log.warning("DNA_SECRET not available, skipping __main__ encryption/verification tests.")

    log.info("To run the FastAPI server, use: uvicorn bando_copilot_core_v1.0.0-BANDO-GODCORE:app --reload")
    # Example: uvicorn.run(app, host="0.0.0.0", port=8000) # Add this if you want it to run from script
    # For now, just logging the command is safer.
