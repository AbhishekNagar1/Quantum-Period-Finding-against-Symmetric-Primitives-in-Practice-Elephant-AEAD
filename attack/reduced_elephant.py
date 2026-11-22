"""
Reduced-Scale Elephant Model for Quantum Simulation.

Preserves the exact algebraic structure of Elephant's Even-Mansour core
while scaling the state width to n in {4, 6, 8} bits so that full
quantum circuit synthesis, superposition evaluation, and statevector
simulations can execute on local quantum simulators (Qiskit Aer).

Structure:
  - Permutation P: Built from Spongent S-box and bit-permutation layer.
  - Mask generation: Reduced-state LFSR progression phi_red.
  - Encryption: E_k(x) = P(x ^ k) ^ k.
  - Periodic function: f(x) = E_k(x) ^ P(x) = P(x ^ k) ^ k ^ P(x).
  - Symmetry: f(x ^ k) = f(x). Hidden period s = k.
"""

from typing import Callable, List, Tuple
from elephant.spongent import SBOX, INV_SBOX


class ReducedElephant4Bit:
    """
    4-bit reduced Elephant model.
    State size: 4 bits (values 0..15).
    Core permutation P: 4-bit Spongent S-box.
    """

    def __init__(self, secret_mask: int = 0b1011):
        if not (0 < secret_mask < 16):
            raise ValueError(f"Secret mask must be a non-zero 4-bit integer, got {secret_mask}")
        self.n = 4
        self.secret_mask = secret_mask
        self.root_mask = secret_mask

    @staticmethod
    def P(x: int) -> int:
        """4-bit Spongent permutation."""
        return SBOX[x & 0x0F]

    def encrypt(self, x: int, mask: int = None) -> int:
        """Even-Mansour encryption: E_k(x) = P(x ^ k) ^ k."""
        k = self.secret_mask if mask is None else mask
        return self.P(x ^ k) ^ k

    def periodic_function(self, x: int, mask: int = None) -> int:
        """
        The Kuwakado-Morii / Bonnetain-Jaques periodic function:
        f(x) = E_k(x) ^ P(x) = P(x ^ k) ^ k ^ P(x)
        Satisfies f(x ^ k) == f(x) for all x.
        """
        k = self.secret_mask if mask is None else mask
        return self.encrypt(x, k) ^ self.P(x)

    def lfsr_step(self, mask: int) -> int:
        """4-bit LFSR mask progression with feedback polynomial x^4 + x + 1."""
        bit = ((mask >> 3) ^ (mask >> 0)) & 1
        return ((mask << 1) | bit) & 0x0F

    def lfsr_inv_step(self, mask: int) -> int:
        """Inverse of 4-bit LFSR progression."""
        lead = (mask >> 0) & 1
        prev_body = (mask >> 1) & 0x07
        # bit = ((prev >> 3) ^ (prev >> 0)) & 1 => lead = prev3 ^ prev0
        # prev0 is (prev >> 0) & 1 = (mask >> 1) & 1. So prev3 = lead ^ prev0
        prev0 = prev_body & 1
        prev3 = lead ^ prev0
        return ((prev3 << 3) | prev_body) & 0x0F


class ReducedElephant8Bit:
    """
    8-bit reduced Elephant model.
    State size: 8 bits (values 0..255).
    Core permutation P: 2 parallel 4-bit Spongent S-boxes + bit shuffle.
    """

    def __init__(self, secret_mask: int = 0b10110101):
        if not (0 < secret_mask < 256):
            raise ValueError(f"Secret mask must be non-zero 8-bit integer, got {secret_mask}")
        self.n = 8
        self.secret_mask = secret_mask
        self.root_mask = secret_mask

    @staticmethod
    def P(x: int) -> int:
        """8-bit permutation: S-box layer + bit permutation."""
        hi = (x >> 4) & 0x0F
        lo = x & 0x0F
        s_hi = SBOX[hi]
        s_lo = SBOX[lo]
        mid = (s_hi << 4) | s_lo

        # 8-bit linear bit-permutation: bit i -> (i * 3) mod 7 for i < 7, 7 -> 7
        out = 0
        for i in range(8):
            bit = (mid >> (7 - i)) & 1
            if bit:
                dest = 7 if i == 7 else (i * 3) % 7
                out |= (1 << (7 - dest))
        return out ^ 0x1F  # Round constant addition

    def encrypt(self, x: int, mask: int = None) -> int:
        """Even-Mansour encryption: E_k(x) = P(x ^ k) ^ k."""
        k = self.secret_mask if mask is None else mask
        return self.P(x ^ k) ^ k

    def periodic_function(self, x: int, mask: int = None) -> int:
        """f(x) = E_k(x) ^ P(x)."""
        k = self.secret_mask if mask is None else mask
        return self.encrypt(x, k) ^ self.P(x)

    def lfsr_step(self, mask: int) -> int:
        """8-bit LFSR step with feedback x^8 + x^4 + x^3 + x^2 + 1."""
        bit = ((mask >> 7) ^ (mask >> 3) ^ (mask >> 2) ^ (mask >> 1)) & 1
        return ((mask << 1) | bit) & 0xFF

    def lfsr_inv_step(self, mask: int) -> int:
        """Inverse 8-bit LFSR step."""
        bit = mask & 1
        prev_body = (mask >> 1) & 0x7F  # bits 0..6 of previous mask
        prev1 = (prev_body >> 1) & 1
        prev2 = (prev_body >> 2) & 1
        prev3 = (prev_body >> 3) & 1
        prev7 = bit ^ prev3 ^ prev2 ^ prev1
        return ((prev7 << 7) | prev_body) & 0xFF
