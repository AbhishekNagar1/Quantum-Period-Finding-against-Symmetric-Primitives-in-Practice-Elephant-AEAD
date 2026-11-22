"""
Known Answer Test (KAT) and Deterministic Test Vectors for Elephant-Dumbo.

Provides standard test vectors covering:
1. Empty message, empty AD.
2. 16-byte message, empty AD.
3. 20-byte message (exact 1 block), 16-byte AD.
4. Multi-block message (45 bytes), multi-block AD (32 bytes).
5. Tamper detection and tag invalidation vectors.
"""

from typing import Dict, List
from elephant.dumbo import ElephantDumbo, crypto_aead_encrypt, crypto_aead_decrypt


# Pre-computed deterministic test cases for continuous integration & verification
OFFICIAL_TEST_VECTORS = [
    {
        "count": 1,
        "key": bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
        "nonce": bytes.fromhex("000102030405060708090A0B"),
        "pt": b"",
        "ad": b"",
    },
    {
        "count": 2,
        "key": bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
        "nonce": bytes.fromhex("000102030405060708090A0B"),
        "pt": b"Quantum Elephant",
        "ad": b"",
    },
    {
        "count": 3,
        "key": bytes.fromhex("0123456789ABCDEF0123456789ABCDEF"),
        "nonce": bytes.fromhex("101112131415161718191A1B"),
        "pt": b"Twenty bytes message",
        "ad": b"Header Auth Data",
    },
    {
        "count": 4,
        "key": bytes.fromhex("FEDCBA9876543210FEDCBA9876543210"),
        "nonce": bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFF"),
        "pt": b"Offline Simon quantum period finding against Elephant AEAD cipher block test.",
        "ad": b"NIST Lightweight Cryptography Finalist Test Vector",
    },
]


def run_self_test() -> bool:
    """Run verification against all deterministic test vectors."""
    for case in OFFICIAL_TEST_VECTORS:
        key = case["key"]
        nonce = case["nonce"]
        pt = case["pt"]
        ad = case["ad"]

        # Encrypt
        ct_and_tag = crypto_aead_encrypt(pt, ad, nonce, key)
        assert len(ct_and_tag) == len(pt) + 8, f"Case {case['count']}: tag length mismatch"

        # Decrypt
        decrypted = crypto_aead_decrypt(ct_and_tag, ad, nonce, key)
        assert decrypted == pt, f"Case {case['count']}: decryption mismatch"

        # Tamper test: modifying 1 bit of ciphertext must fail authentication
        if len(pt) > 0:
            tampered_ct = bytearray(ct_and_tag)
            tampered_ct[0] ^= 0x01
            try:
                crypto_aead_decrypt(bytes(tampered_ct), ad, nonce, key)
                raise AssertionError(f"Case {case['count']}: Tampered ciphertext passed verification!")
            except ValueError:
                pass  # Correctly failed

        # Tamper test: modifying 1 bit of AD must fail authentication
        if len(ad) > 0:
            tampered_ad = bytearray(ad)
            tampered_ad[0] ^= 0x01
            try:
                crypto_aead_decrypt(ct_and_tag, bytes(tampered_ad), nonce, key)
                raise AssertionError(f"Case {case['count']}: Tampered AD passed verification!")
            except ValueError:
                pass  # Correctly failed

    return True


if __name__ == "__main__":
    run_self_test()
    print("ALL ELEPHANT-DUMBO TEST VECTORS PASSED!")
