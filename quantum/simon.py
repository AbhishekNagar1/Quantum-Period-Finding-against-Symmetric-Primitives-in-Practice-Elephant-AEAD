"""
Simon's Quantum Algorithm Implementation using Qiskit.

Algorithm Steps:
1. Initialize n-qubit query register |x> and n-qubit output register |y>.
2. Apply Hadamard gates H^⊗n to query register |x>.
3. Evaluate quantum oracle U_f: |x>|y> -> |x>|y ^ f(x)>.
4. Apply Hadamard gates H^⊗n to query register |x>.
5. Measure query register |x> into classical register.
6. Each measurement yields a bitstring y such that y . s = 0 (mod 2).
7. Collect equations and solve using GF(2) Gaussian elimination.
8. Verify recovered secret period s.
"""

from typing import Dict, List, Optional, Tuple, Union
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from quantum.gf2_solver import GF2Solver
from quantum.oracle import CanonicalSimonOracle


class SimonsAlgorithm:
    """
    Executes Simon's period finding quantum algorithm.
    """

    def __init__(self, oracle_circuit: QuantumCircuit, n_bits: int):
        self.oracle_circuit = oracle_circuit
        self.n = n_bits
        self.backend = AerSimulator()
        self.circuit: Optional[QuantumCircuit] = None

    def build_circuit(self) -> QuantumCircuit:
        """Construct the complete Simon quantum circuit."""
        qr_in = QuantumRegister(self.n, name="x")
        qr_out = QuantumRegister(self.n, name="y")
        cr = ClassicalRegister(self.n, name="meas")
        qc = QuantumCircuit(qr_in, qr_out, cr, name="Simons_Algorithm")

        # 1. Hadamard on query register
        qc.h(qr_in)
        qc.barrier()

        # 2. Append Oracle U_f
        qc.compose(self.oracle_circuit, qubits=list(qr_in) + list(qr_out), inplace=True)
        qc.barrier()

        # 3. Hadamard on query register
        qc.h(qr_in)
        qc.barrier()

        # 4. Measure query register
        qc.measure(qr_in, cr)

        self.circuit = qc
        return qc

    def run(
        self,
        shots: int = 1024,
        max_samples: Optional[int] = None,
        verifier_fn: Optional[Callable[[str], bool]] = None,
    ) -> Tuple[Optional[str], Dict[str, int], int]:
        """
        Execute Simon's algorithm on AerSimulator.
        Returns:
            - recovered_period: Binary string e.g. '110' (or None if failed)
            - measurement_counts: Dict of measured bitstrings and frequencies
            - total_queries: Number of independent measurement samples used
        """
        if self.circuit is None:
            self.build_circuit()

        # Execute simulation
        # Note: Qiskit 2.x AerSimulator supports run() directly on circuits
        job = self.backend.run(self.circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()

        # Classical post-processing with GF(2) Gaussian Elimination
        solver = GF2Solver(self.n)
        queries_used = 0

        # Sort measured bitstrings by frequency
        sorted_samples = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        for bitstr, freq in sorted_samples:
            # Qiskit bitstring order is little-endian (qubit 0 is rightmost)
            # Reverse to match big-endian indexing (qubit 0 is leftmost)
            norm_bitstr = bitstr[::-1]
            queries_used += 1

            solver.add_equation(norm_bitstr)
            if solver.is_solvable():
                break

            if max_samples is not None and queries_used >= max_samples:
                break

        recovered_period = solver.solve_as_bitstring(verifier_fn=verifier_fn)
        return recovered_period, counts, queries_used


def run_simon_for_period(
    secret_period: Union[str, List[int]],
    shots: int = 1024,
) -> Tuple[Optional[str], bool, Dict[str, int]]:
    """
    Convenience function to run Simon's algorithm on a known secret period.
    Returns: (recovered_period, is_correct, counts)
    """
    if isinstance(secret_period, list):
        target = "".join(str(b) for b in secret_period)
    else:
        target = str(secret_period)

    oracle = CanonicalSimonOracle(target)
    simon = SimonsAlgorithm(oracle.to_circuit(), len(target))
    recovered, counts, _ = simon.run(shots=shots)

    is_correct = (recovered == target)
    return recovered, is_correct, counts
