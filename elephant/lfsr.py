"""
LFSR and Mask Generation Module for Elephant-Dumbo.

In Elephant, masks are derived from the key and advanced through a
word-oriented Linear Feedback Shift Register (LFSR) operation phi.
For Dumbo (160 bits / 20 bytes):
  feedback = rotl3(input[0]) ^ (input[3] << 7) ^ (input[13] >> 7)
  output = input[1..19] || feedback

This module implements:
1. rotl3 and rotr3 bitwise byte rotations.
2. Forward LFSR step (phi).
3. Inverse LFSR step (phi^-1).
4. Arbitrary power mask advancement phi^k and phi^-k.
5. Mask derivation from key.
"""

from typing import Union


BLOCK_SIZE = 20  # 160 bits for Dumbo


def rotl(b: int, shift: int) -> int:
    """Rotate 8-bit integer left by shift bits."""
    shift %= 8
    return (((b << shift) | (b >> (8 - shift)))) & 0xFF


def rotr(b: int, shift: int) -> int:
    """Rotate 8-bit integer right by shift bits."""
    shift %= 8
    return (((b >> shift) | (b << (8 - shift)))) & 0xFF


def rotl3(b: int) -> int:
    """Rotate 8-bit byte left by 3 positions."""
    return rotl(b, 3)


def rotr3(b: int) -> int:
    """Rotate 8-bit byte right by 3 positions (inverse of rotl3)."""
    return rotr(b, 3)


def lfsr_step(state: Union[bytes, bytearray]) -> bytes:
    """
    Compute forward step of the Dumbo LFSR phi:
    output[i] = input[i + 1] for i in 0..18
    output[19] = rotl3(input[0]) ^ (input[3] << 7) ^ (input[13] >> 7)
    """
    if len(state) != BLOCK_SIZE:
        raise ValueError(f"State must be {BLOCK_SIZE} bytes, got {len(state)}")

    inp = bytes(state)
    feedback = (
        rotl3(inp[0])
        ^ ((inp[3] << 7) & 0xFF)
        ^ (inp[13] >> 7)
    ) & 0xFF

    out = bytearray(BLOCK_SIZE)
    for i in range(BLOCK_SIZE - 1):
        out[i] = inp[i + 1]
    out[BLOCK_SIZE - 1] = feedback

    return bytes(out)


def lfsr_inv_step(state: Union[bytes, bytearray]) -> bytes:
    """
    Compute inverse step of the Dumbo LFSR phi^-1:
    input[1..19] = output[0..18]
    input[0] = rotr3(output[19] ^ (input[3] << 7) ^ (input[13] >> 7))
             = rotr3(output[19] ^ (output[2] << 7) ^ (output[12] >> 7))
    """
    if len(state) != BLOCK_SIZE:
        raise ValueError(f"State must be {BLOCK_SIZE} bytes, got {len(state)}")

    out = bytes(state)
    inp = bytearray(BLOCK_SIZE)

    # Reconstruct input[1..19]
    for i in range(BLOCK_SIZE - 1):
        inp[i + 1] = out[i]

    # Reconstruct input[0]
    term = (out[BLOCK_SIZE - 1] ^ ((inp[3] << 7) & 0xFF) ^ (inp[13] >> 7)) & 0xFF
    inp[0] = rotr3(term)

    return bytes(inp)


def lfsr_step_k(state: Union[bytes, bytearray], k: int) -> bytes:
    """Advance or rewind LFSR state by k steps (k >= 0 forward, k < 0 backward)."""
    current = bytes(state)
    if k >= 0:
        for _ in range(k):
            current = lfsr_step(current)
    else:
        for _ in range(-k):
            current = lfsr_inv_step(current)
    return current


def derive_root_mask(key: bytes, permutation_fn) -> bytes:
    """
    Derive initial root mask M_0 from 128-bit master key K:
    K' = K || 0^(160 - 128)  (16 bytes padded to 20 bytes)
    M_0 = P(K') ^ K'
    """
    if len(key) != 16:
        raise ValueError(f"Dumbo master key must be 16 bytes (128 bits), got {len(key)}")

    padded_key = bytearray(BLOCK_SIZE)
    padded_key[:16] = key

    permuted = permutation_fn(padded_key)
    root_mask = bytes(p ^ k for p, k in zip(permuted, padded_key))
    return root_mask
