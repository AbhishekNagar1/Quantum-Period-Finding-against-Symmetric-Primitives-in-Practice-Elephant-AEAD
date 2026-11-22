"""Unit tests for Elephant-Dumbo implementation."""

import pytest
import os
from elephant.spongent import (
    spongent_pi_160,
    sbox_layer,
    player,
    step_lcounter,
    retnuocl,
    SBOX,
    INV_SBOX,
)
from elephant.lfsr import (
    BLOCK_SIZE,
    rotl3,
    rotr3,
    lfsr_step,
    lfsr_inv_step,
    lfsr_step_k,
    derive_root_mask,
)
from elephant.dumbo import (
    ElephantDumbo,
    crypto_aead_encrypt,
    crypto_aead_decrypt,
    pad_block,
    pad_nonce,
)
from elephant.test_vectors import run_self_test, OFFICIAL_TEST_VECTORS


def test_sbox_invertibility():
    """Verify S-box is a bijective 4-bit permutation."""
    assert len(set(SBOX)) == 16
    for x in range(16):
        y = SBOX[x]
        assert INV_SBOX[y] == x


def test_player_invertibility():
    """Verify pLayer is a bijective 160-bit permutation."""
    for byte_pos in range(20):
        for bit_pos in range(8):
            st = bytearray(20)
            st[byte_pos] |= (1 << bit_pos)
            player(st)
            # Must have exactly 1 bit set
            total_bits = sum(bin(b).count("1") for b in st)
            assert total_bits == 1


def test_spongent_determinism_and_length():
    """Verify Spongent-pi[160] outputs exactly 20 bytes and is deterministic."""
    data = os.urandom(20)
    out1 = spongent_pi_160(data)
    out2 = spongent_pi_160(data)
    assert len(out1) == 20
    assert out1 == out2
    assert out1 != data  # Non-trivial transformation


def test_lfsr_roundtrip():
    """Verify forward and inverse LFSR steps are exact inverses."""
    for _ in range(50):
        mask = os.urandom(20)
        fwd = lfsr_step(mask)
        rev = lfsr_inv_step(fwd)
        assert rev == mask

        # Multi-step
        fwd_5 = lfsr_step_k(mask, 5)
        rev_5 = lfsr_step_k(fwd_5, -5)
        assert rev_5 == mask


def test_elephant_encrypt_decrypt_symmetry():
    """Verify decryption perfectly recovers original plaintext across various lengths."""
    key = os.urandom(16)
    nonce = os.urandom(12)

    for length in [0, 1, 5, 16, 20, 21, 40, 63, 100]:
        pt = os.urandom(length)
        ad = os.urandom(length // 2) if length > 0 else b""

        ct_tag = crypto_aead_encrypt(pt, ad, nonce, key)
        assert len(ct_tag) == length + 8

        recovered = crypto_aead_decrypt(ct_tag, ad, nonce, key)
        assert recovered == pt


def test_elephant_tamper_detection():
    """Verify modifying ciphertext, tag, nonce, or AD raises ValueError."""
    key = os.urandom(16)
    nonce = os.urandom(12)
    pt = b"Critical cryptographic payload"
    ad = b"Authentic Associated Data"

    ct_tag = crypto_aead_encrypt(pt, ad, nonce, key)

    # 1. Tamper ciphertext
    tampered_ct = bytearray(ct_tag)
    tampered_ct[5] ^= 0xFF
    with pytest.raises(ValueError):
        crypto_aead_decrypt(bytes(tampered_ct), ad, nonce, key)

    # 2. Tamper tag
    tampered_tag = bytearray(ct_tag)
    tampered_tag[-1] ^= 0x01
    with pytest.raises(ValueError):
        crypto_aead_decrypt(bytes(tampered_tag), ad, nonce, key)

    # 3. Tamper AD
    with pytest.raises(ValueError):
        crypto_aead_decrypt(ct_tag, b"Corrupted AD", nonce, key)

    # 4. Tamper Nonce
    tampered_nonce = bytearray(nonce)
    tampered_nonce[0] ^= 0x01
    with pytest.raises(ValueError):
        crypto_aead_decrypt(ct_tag, ad, bytes(tampered_nonce), key)


def test_official_test_vectors():
    """Run full deterministic KAT test suite."""
    assert run_self_test() is True
