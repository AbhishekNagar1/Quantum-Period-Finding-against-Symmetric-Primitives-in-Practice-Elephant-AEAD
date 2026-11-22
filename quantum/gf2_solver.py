"""
Linear Algebra and Gaussian Elimination over GF(2).

Solves the linear system:
    M * s = 0 (mod 2)
given a set of measurement bitstrings y produced by Simon's quantum subroutine,
where each y satisfies:
    y . s = sum_j (y_j * s_j) = 0 (mod 2).

Includes:
1. Matrix rank computation over GF(2).
2. Elimination to reduced row-echelon form (RREF).
3. Non-trivial nullspace (kernel) basis extraction.
4. Verification that candidate period satisfies all equations.
"""

from typing import Callable, List, Optional, Union
import numpy as np


class GF2Solver:
    """
    Gaussian Elimination solver over Galois Field GF(2).
    """

    def __init__(self, n_bits: int):
        self.n = n_bits
        self.equations: List[List[int]] = []

    def add_equation(self, vector: Union[str, List[int], np.ndarray]) -> bool:
        """
        Add a measurement equation vector y (as bitstring e.g. '101' or list of ints).
        Returns True if the new equation is linearly independent, False if redundant.
        """
        if isinstance(vector, str):
            vec = [int(c) for c in vector]
        elif isinstance(vector, np.ndarray):
            vec = [int(x) for x in vector]
        else:
            vec = list(vector)

        if len(vec) != self.n:
            raise ValueError(f"Vector length {len(vec)} does not match solver dimension {self.n}")

        # Check if non-zero
        if not any(vec):
            return False

        # Try to insert into row echelon basis
        current = list(vec)
        for eq in self.equations:
            lead = self._leading_index(eq)
            if lead != -1 and current[lead] == 1:
                # XOR subtract equation
                current = [c ^ e for c, e in zip(current, eq)]

        if any(current):
            self.equations.append(current)
            # Keep sorted by leading index
            self.equations.sort(key=self._leading_index)
            return True
        return False

    @staticmethod
    def _leading_index(row: List[int]) -> int:
        """Return the index of the first 1 in row, or -1 if all zeros."""
        for idx, val in enumerate(row):
            if val == 1:
                return idx
        return -1

    @property
    def rank(self) -> int:
        """Current rank of the linear system over GF(2)."""
        return len(self.equations)

    def is_solvable(self) -> bool:
        """Check if we have collected n - 1 linearly independent equations."""
        return self.rank >= self.n - 1

    def get_nullspace_basis(self) -> List[List[int]]:
        """
        Extract a basis for the right kernel (nullspace) M * s = 0 (mod 2).
        Returns a list of basis vectors.
        """
        rows = [list(eq) for eq in self.equations]
        k = len(rows)
        if k == 0:
            return []

        # Back-substitution to RREF
        for i in range(k - 1, -1, -1):
            pivot = self._leading_index(rows[i])
            for j in range(i):
                if rows[j][pivot] == 1:
                    rows[j] = [r ^ p for r, p in zip(rows[j], rows[i])]

        pivot_cols = set(self._leading_index(r) for r in rows)
        free_cols = [c for c in range(self.n) if c not in pivot_cols]

        basis = []
        for free_var in free_cols:
            vec = [0] * self.n
            vec[free_var] = 1
            for row in rows:
                lead = self._leading_index(row)
                if lead != -1 and lead != free_var:
                    vec[lead] = row[free_var]
            basis.append(vec)

        return basis

    def get_nullspace_vectors(self) -> List[List[int]]:
        """
        Generate all non-zero vectors in the nullspace.
        """
        basis = self.get_nullspace_basis()
        if not basis:
            return []

        num_free = len(basis)
        vectors = []
        for combo in range(1, 1 << num_free):
            vec = [0] * self.n
            for i in range(num_free):
                if (combo >> i) & 1:
                    vec = [v ^ b for v, b in zip(vec, basis[i])]
            vectors.append(vec)

        return vectors

    def solve(self, verifier_fn: Optional[Callable[[List[int]], bool]] = None) -> Optional[List[int]]:
        """
        Solve M * s = 0 (mod 2) for non-zero period vector s.
        If multiple nullspace vectors exist (e.g. rank n-2 due to chance collisions),
        uses verifier_fn to pick the true cryptographic period.
        """
        vectors = self.get_nullspace_vectors()
        if not vectors:
            return None

        if verifier_fn is not None:
            for cand in vectors:
                if verifier_fn(cand):
                    return cand

        # Default to first non-zero vector in nullspace
        return vectors[0]

    def solve_as_bitstring(self, verifier_fn: Optional[Callable[[str], bool]] = None) -> Optional[str]:
        """Solve and return period s as binary string (e.g., '1010')."""
        def list_verifier(vec: List[int]) -> bool:
            if verifier_fn is None:
                return True
            return verifier_fn("".join(str(b) for b in vec))

        sol = self.solve(verifier_fn=list_verifier if verifier_fn else None)
        if sol is None:
            return None
        return "".join(str(b) for b in sol)

    def verify_solution(self, s: List[int]) -> bool:
        """Verify that s is non-zero and satisfies all recorded equations."""
        if not any(s):
            return False
        for eq in self.equations:
            dot = sum(a * b for a, b in zip(eq, s)) % 2
            if dot != 0:
                return False
        return True
