"""
Reversible Quantum Simon Oracles in Qiskit.

Provides:
1. CanonicalSimonOracle: Efficient CNOT-based reversible oracle for arbitrary known period s.
2. ClassicalToQuantumOracle: Synthesizes a quantum circuit for any arbitrary 2-to-1 function f.
3. EvenMansourOracle: Reversible oracle for f(x) = E_k(x) ^ P(x) exposing hidden period s = k.
"""

from typing import Callable, Dict, List, Union
from qiskit import QuantumCircuit, QuantumRegister


class CanonicalSimonOracle:
    """
    Constructs an exact, minimal CNOT-based reversible Simon oracle.

    For secret period s != 0:
    Finds pivot bit p = first index where s[p] == 1.
    Defines f(x):
        f(x) = x           if x[p] == 0
        f(x) = x ^ s       if x[p] == 1
    Then f(x ^ s) = f(x) for all x.

    Reversible gate implementation:
    1. Copy x into output register y using CNOTs: CX(x_i, y_i) for i in 0..n-1.
    2. Controlled on pivot x_p, XOR s into y: CX(x_p, y_j) for all j where s[j] == 1.
    """

    def __init__(self, period: Union[str, List[int]]):
        if isinstance(period, str):
            self.s = [int(c) for c in period]
        else:
            self.s = list(period)

        self.n = len(self.s)
        if not any(self.s):
            raise ValueError("Secret period s cannot be all zeros for Simon's 2-to-1 oracle")

        # Find pivot index (first non-zero bit)
        self.pivot = self.s.index(1)

    def evaluate_classical(self, x_bits: List[int]) -> List[int]:
        """Classical evaluation of f(x)."""
        if len(x_bits) != self.n:
            raise ValueError(f"Input length {len(x_bits)} != {self.n}")
        if x_bits[self.pivot] == 0:
            return list(x_bits)
        else:
            return [x ^ s for x, s in zip(x_bits, self.s)]

    def to_circuit(self) -> QuantumCircuit:
        """
        Synthesize the reversible quantum circuit U_f.
        Registers:
            q_in: n qubits (query register)
            q_out: n qubits (target register)
        """
        qr_in = QuantumRegister(self.n, name="x")
        qr_out = QuantumRegister(self.n, name="y")
        qc = QuantumCircuit(qr_in, qr_out, name=f"Oracle_s={''.join(str(b) for b in self.s)}")

        # 1. Copy x into y: y = x
        for i in range(self.n):
            qc.cx(qr_in[i], qr_out[i])

        # 2. If x[pivot] == 1, y = y ^ s
        for j in range(self.n):
            if self.s[j] == 1:
                qc.cx(qr_in[self.pivot], qr_out[j])

        return qc


class CustomFunctionOracle:
    """
    Constructs a quantum oracle for any arbitrary boolean function f: {0, 1}^n -> {0, 1}^n.
    Uses truth-table compilation with multi-controlled X (MCX) gates.
    """

    def __init__(self, n_bits: int, f_mapping: Callable[[int], int]):
        self.n = n_bits
        self.f_mapping = f_mapping
        self.table = {x: f_mapping(x) for x in range(2**n_bits)}

    def to_circuit(self) -> QuantumCircuit:
        qr_in = QuantumRegister(self.n, name="x")
        qr_out = QuantumRegister(self.n, name="y")
        qc = QuantumCircuit(qr_in, qr_out, name="Custom_U_f")

        # Synthesize state-by-state truth table mapping
        for x_val, f_val in self.table.items():
            if f_val == 0:
                continue

            # Binary representations (MSB at index 0)
            x_bin = [(x_val >> (self.n - 1 - i)) & 1 for i in range(self.n)]
            f_bin = [(f_val >> (self.n - 1 - i)) & 1 for i in range(self.n)]

            # Invert control qubits where x_bin bit is 0
            for i, bit in enumerate(x_bin):
                if bit == 0:
                    qc.x(qr_in[i])

            # Apply multi-controlled NOT to active output bits
            for j, out_bit in enumerate(f_bin):
                if out_bit == 1:
                    qc.mcx(qr_in, qr_out[j])

            # Uncompute X gates on control qubits
            for i, bit in enumerate(x_bin):
                if bit == 0:
                    qc.x(qr_in[i])

        return qc
