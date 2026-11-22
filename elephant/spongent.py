"""
Spongent-pi[160] Permutation Module for Elephant-Dumbo.

Spongent is a lightweight permutation based on a Substitution-Permutation
Network (SPN). Spongent-pi[160] operates on a 160-bit (20-byte) state
for 80 rounds using a 4-bit S-box, a bit-permutation layer (pLayer),
and an LFSR-driven round counter (lCounter).
"""

from typing import List, Union

# 4-bit S-box for Spongent
SBOX = [
    0x0E, 0x04, 0x0B, 0x01, 0x07, 0x09, 0x0F, 0x03,
    0x00, 0x0C, 0x05, 0x02, 0x0A, 0x0D, 0x08, 0x06
]

# Inverse S-box (for reference and reversible circuit synthesis)
INV_SBOX = [
    0x08, 0x03, 0x0B, 0x07, 0x01, 0x0A, 0x0F, 0x04,
    0x0E, 0x05, 0x0C, 0x02, 0x09, 0x0D, 0x00, 0x06
]

STATE_SIZE_BYTES = 20
STATE_SIZE_BITS = 160
N_ROUNDS = 80
LFSR_IV = 0x75  # Initial 7-bit LFSR value for Spongent-pi[160] (80 rounds)


def step_lcounter(lfsr: int) -> int:
    """Step the 7-bit LFSR counter using primitive polynomial x^7 + x^6 + 1."""
    bit = ((lfsr >> 6) ^ (lfsr >> 5)) & 1
    lfsr = ((lfsr << 1) | bit) & 0x7F
    return lfsr


def retnuocl(lfsr: int) -> int:
    """
    Reverse the 7-bit LFSR value and align it into an 8-bit byte.
    Bit 0 -> Bit 7, Bit 1 -> Bit 6, ..., Bit 6 -> Bit 1.
    """
    res = (
        ((lfsr & 0x01) << 7)
        | ((lfsr & 0x02) << 5)
        | ((lfsr & 0x04) << 3)
        | ((lfsr & 0x08) << 1)
        | ((lfsr & 0x10) >> 1)
        | ((lfsr & 0x20) >> 3)
        | ((lfsr & 0x40) >> 5)
    )
    return res & 0xFF


def sbox_layer(state: bytearray) -> None:
    """Apply 4-bit S-box to all 40 nibbles of the 160-bit state."""
    for i in range(len(state)):
        b = state[i]
        hi = (b >> 4) & 0x0F
        lo = b & 0x0F
        state[i] = ((SBOX[hi] << 4) | SBOX[lo]) & 0xFF


def player(state: bytearray) -> None:
    """
    Apply bit permutation layer pLayer to the 160-bit state.
    P(j) = (j * 40) mod 159 for 0 <= j <= 158, P(159) = 159.
    Bit 0 is MSB of byte 0: (state[j // 8] >> (7 - (j % 8))) & 1.
    """
    out = bytearray(STATE_SIZE_BYTES)
    for j in range(160):
        # Extract bit j
        byte_idx = j // 8
        bit_idx = 7 - (j % 8)
        bit = (state[byte_idx] >> bit_idx) & 1

        if bit:
            # Destination bit
            dest_j = 159 if j == 159 else (j * 40) % 159
            dest_byte = dest_j // 8
            dest_bit = 7 - (dest_j % 8)
            out[dest_byte] |= (1 << dest_bit)

    state[:] = out


def spongent_pi_160(input_bytes: Union[bytes, bytearray]) -> bytes:
    """
    Execute 80-round Spongent-pi[160] permutation.
    Input must be exactly 20 bytes (160 bits).
    Returns 20 bytes.
    """
    if len(input_bytes) != STATE_SIZE_BYTES:
        raise ValueError(f"Spongent-pi[160] requires exactly {STATE_SIZE_BYTES} bytes, got {len(input_bytes)}")

    state = bytearray(input_bytes)
    lfsr = LFSR_IV

    for _ in range(N_ROUNDS):
        # 1. Add round counter
        state[0] ^= lfsr
        state[STATE_SIZE_BYTES - 1] ^= retnuocl(lfsr)

        # 2. S-box substitution layer
        sbox_layer(state)

        # 3. Linear bit-permutation layer
        player(state)

        # 4. Advance LFSR
        lfsr = step_lcounter(lfsr)

    return bytes(state)
