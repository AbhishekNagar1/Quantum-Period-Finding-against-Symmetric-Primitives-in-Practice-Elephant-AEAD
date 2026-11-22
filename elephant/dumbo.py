"""
Elephant-Dumbo Authenticated Encryption with Associated Data (AEAD).

Elephant is a family of lightweight, parallelizable, inverse-free AEAD schemes
designed for constrained environments (NIST Lightweight Cryptography Finalist).

Dumbo Parameters:
  - Underlying Permutation: Spongent-pi[160] (80 rounds)
  - Permutation / State size: 160 bits (20 bytes)
  - Key size: 128 bits (16 bytes)
  - Nonce size: 96 bits (12 bytes)
  - Authentication Tag size: 64 bits (8 bytes)
  - Security level: 112 bits

Mode of Operation:
  - Masked Even-Mansour-like counter encryption.
  - Linear Feedback Shift Register (LFSR) mask progression phi.
  - Inverse-free permutation: only forward P evaluations are used.
  - Tag verification in constant time.
"""

from typing import Tuple, Union
import hmac
from elephant.spongent import spongent_pi_160
from elephant.lfsr import (
    BLOCK_SIZE,
    lfsr_step,
    lfsr_inv_step,
    derive_root_mask,
)

KEY_BYTES = 16    # 128 bits
NONCE_BYTES = 12  # 96 bits
TAG_BYTES = 8     # 64 bits


def pad_block(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    """
    Pad a block shorter than block_size using standard 0x01 || 0x00... padding.
    If len(data) == block_size, returns data unchanged.
    """
    if len(data) == block_size:
        return data
    pad_len = block_size - len(data)
    return data + b"\x01" + b"\x00" * (pad_len - 1)


def pad_nonce(nonce: bytes) -> bytes:
    """Pad 12-byte (96-bit) nonce to 20-byte (160-bit) block with zeros."""
    if len(nonce) != NONCE_BYTES:
        raise ValueError(f"Nonce must be exactly {NONCE_BYTES} bytes, got {len(nonce)}")
    return nonce + b"\x00" * (BLOCK_SIZE - NONCE_BYTES)


class ElephantDumbo:
    """
    Elephant-Dumbo AEAD implementation.
    """

    def __init__(self, key: bytes):
        if len(key) != KEY_BYTES:
            raise ValueError(f"Key must be exactly {KEY_BYTES} bytes (128 bits), got {len(key)}")
        self.key = bytes(key)
        # Derive initial root mask M_0 = P(K || 0) ^ (K || 0)
        self.root_mask = derive_root_mask(self.key, spongent_pi_160)

    def get_mask(self, step: int) -> bytes:
        """
        Derive mask at step index using LFSR progression phi.
        step 0 is root_mask.
        """
        mask = self.root_mask
        for _ in range(step):
            mask = lfsr_step(mask)
        return mask

    def encrypt_block(self, padded_nonce: bytes, mask: bytes) -> bytes:
        """
        Compute Even-Mansour keystream block for nonce N' and mask:
        Z = P(N' ^ mask) ^ mask ^ N'
        """
        masked_input = bytes(n ^ m for n, m in zip(padded_nonce, mask))
        permuted = spongent_pi_160(masked_input)
        keystream = bytes(p ^ m ^ n for p, m, n in zip(permuted, mask, padded_nonce))
        return keystream

    def authenticate_block(self, block: bytes, mask: bytes) -> bytes:
        """
        Compute MAC contribution for an input block:
        T_i = P(block ^ mask) ^ mask
        """
        masked = bytes(b ^ m for b, m in zip(block, mask))
        permuted = spongent_pi_160(masked)
        return bytes(p ^ m for p, m in zip(permuted, mask))

    def encrypt(
        self,
        nonce: bytes,
        plaintext: bytes,
        associated_data: bytes = b"",
    ) -> bytes:
        """
        Authenticated encryption of plaintext with nonce and optional associated data.
        Returns ciphertext concatenated with 8-byte authentication tag: C || T.
        """
        if len(nonce) != NONCE_BYTES:
            raise ValueError(f"Nonce must be {NONCE_BYTES} bytes, got {len(nonce)}")

        padded_nonce = pad_nonce(nonce)
        pt_len = len(plaintext)

        # 1. Encryption phase (Counter mode with masks)
        ciphertext = bytearray()
        num_blocks = (pt_len + BLOCK_SIZE - 1) // BLOCK_SIZE if pt_len > 0 else 0

        # We maintain rolling masks: current_mask advances via lfsr_step
        current_mask = self.root_mask
        # Tag accumulator initialized with nonce contribution: P(N' ^ M_0) ^ M_0
        tag_acc = bytearray(self.authenticate_block(padded_nonce, self.root_mask))

        for i in range(num_blocks):
            # Advance mask for block encryption
            current_mask = lfsr_step(current_mask)
            block_start = i * BLOCK_SIZE
            block_end = min(block_start + BLOCK_SIZE, pt_len)
            pt_chunk = plaintext[block_start:block_end]

            keystream = self.encrypt_block(padded_nonce, current_mask)
            ct_chunk = bytes(p ^ k for p, k in zip(pt_chunk, keystream[: len(pt_chunk)]))
            ciphertext.extend(ct_chunk)

            # Accumulate ciphertext block into tag
            padded_ct = pad_block(ct_chunk, BLOCK_SIZE)
            ct_tag_contrib = self.authenticate_block(padded_ct, current_mask)
            for j in range(BLOCK_SIZE):
                tag_acc[j] ^= ct_tag_contrib[j]

        # 2. Process Associated Data into tag
        ad_len = len(associated_data)
        if ad_len > 0:
            num_ad_blocks = (ad_len + BLOCK_SIZE - 1) // BLOCK_SIZE
            ad_mask = self.root_mask
            for i in range(num_ad_blocks):
                # Using secondary mask progression for AD domain separation
                ad_mask = lfsr_step(lfsr_step(ad_mask))
                ad_start = i * BLOCK_SIZE
                ad_end = min(ad_start + BLOCK_SIZE, ad_len)
                ad_chunk = associated_data[ad_start:ad_end]
                padded_ad = pad_block(ad_chunk, BLOCK_SIZE)

                ad_contrib = self.authenticate_block(padded_ad, ad_mask)
                for j in range(BLOCK_SIZE):
                    tag_acc[j] ^= ad_contrib[j]

        # 3. Finalize tag: truncate to TAG_BYTES (8 bytes)
        tag = bytes(tag_acc[:TAG_BYTES])

        return bytes(ciphertext) + tag

    def decrypt(
        self,
        nonce: bytes,
        ciphertext_and_tag: bytes,
        associated_data: bytes = b"",
    ) -> bytes:
        """
        Decryption and authentication verification.
        ciphertext_and_tag must contain at least TAG_BYTES (8 bytes).
        Returns plaintext if tag is valid; raises ValueError if verification fails.
        """
        if len(ciphertext_and_tag) < TAG_BYTES:
            raise ValueError(f"Ciphertext must be at least {TAG_BYTES} bytes (tag size)")

        ct_len = len(ciphertext_and_tag) - TAG_BYTES
        ciphertext = ciphertext_and_tag[:ct_len]
        received_tag = ciphertext_and_tag[ct_len:]

        padded_nonce = pad_nonce(nonce)
        num_blocks = (ct_len + BLOCK_SIZE - 1) // BLOCK_SIZE if ct_len > 0 else 0

        # Decrypt ciphertext
        plaintext = bytearray()
        current_mask = self.root_mask
        tag_acc = bytearray(self.authenticate_block(padded_nonce, self.root_mask))

        for i in range(num_blocks):
            current_mask = lfsr_step(current_mask)
            block_start = i * BLOCK_SIZE
            block_end = min(block_start + BLOCK_SIZE, ct_len)
            ct_chunk = ciphertext[block_start:block_end]

            keystream = self.encrypt_block(padded_nonce, current_mask)
            pt_chunk = bytes(c ^ k for c, k in zip(ct_chunk, keystream[: len(ct_chunk)]))
            plaintext.extend(pt_chunk)

            # Accumulate ciphertext into expected tag
            padded_ct = pad_block(ct_chunk, BLOCK_SIZE)
            ct_tag_contrib = self.authenticate_block(padded_ct, current_mask)
            for j in range(BLOCK_SIZE):
                tag_acc[j] ^= ct_tag_contrib[j]

        # Process Associated Data
        ad_len = len(associated_data)
        if ad_len > 0:
            num_ad_blocks = (ad_len + BLOCK_SIZE - 1) // BLOCK_SIZE
            ad_mask = self.root_mask
            for i in range(num_ad_blocks):
                ad_mask = lfsr_step(lfsr_step(ad_mask))
                ad_start = i * BLOCK_SIZE
                ad_end = min(ad_start + BLOCK_SIZE, ad_len)
                ad_chunk = associated_data[ad_start:ad_end]
                padded_ad = pad_block(ad_chunk, BLOCK_SIZE)

                ad_contrib = self.authenticate_block(padded_ad, ad_mask)
                for j in range(BLOCK_SIZE):
                    tag_acc[j] ^= ad_contrib[j]

        expected_tag = bytes(tag_acc[:TAG_BYTES])

        # Constant-time comparison
        if not hmac.compare_digest(received_tag, expected_tag):
            raise ValueError("Authentication verification failed: invalid tag!")

        return bytes(plaintext)


# NIST Standard Function Wrappers
def crypto_aead_encrypt(
    message: bytes,
    associated_data: bytes,
    nonce: bytes,
    key: bytes,
) -> bytes:
    """Standard NIST AEAD encryption wrapper."""
    cipher = ElephantDumbo(key)
    return cipher.encrypt(nonce, message, associated_data)


def crypto_aead_decrypt(
    ciphertext_and_tag: bytes,
    associated_data: bytes,
    nonce: bytes,
    key: bytes,
) -> bytes:
    """Standard NIST AEAD decryption wrapper."""
    cipher = ElephantDumbo(key)
    return cipher.decrypt(nonce, ciphertext_and_tag, associated_data)
