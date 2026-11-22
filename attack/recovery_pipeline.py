"""
End-to-End Elephant Quantum Attack Pipeline.

Workflow:
1. Target: Reduced Elephant model with unknown secret mask k = mask_i.
2. Construct Quantum Oracle for f(x) = E_k(x) ^ P(x).
3. Execute Simon's Algorithm on Qiskit Aer.
4. Collect measurement vectors y where y . s = 0 (mod 2).
5. Solve linear system using GF(2) Gaussian Elimination.
6. Extract recovered period s.
7. Verify s == mask_i.
8. Apply LFSR inverse phi^-i to recover root mask M_0.
9. Verify M_0 == initial experimental secret.
"""

from typing import Any, Dict, Optional, Tuple, Union
from quantum.simon import SimonsAlgorithm
from attack.reduced_elephant import ReducedElephant4Bit, ReducedElephant8Bit
from attack.attack_oracle import build_elephant_attack_oracle


class ElephantAttackPipeline:
    """
    Automated attack execution and verification pipeline.
    """

    def __init__(
        self,
        model: Union[ReducedElephant4Bit, ReducedElephant8Bit],
        step_index: int = 1,
    ):
        self.model = model
        self.step = step_index
        self.n = model.n

        # Derive active block mask for step: mask_i = phi^i(M_0)
        curr = model.root_mask
        for _ in range(step_index):
            curr = model.lfsr_step(curr)
        self.active_mask = curr

    def execute_attack(
        self,
        shots: int = 2048,
    ) -> Dict[str, Any]:
        """
        Run the complete quantum attack and return verification report.
        """
        # 1. Synthesize quantum oracle for the active block mask
        oracle_qc = build_elephant_attack_oracle(self.model, self.active_mask)

        # Verification helper: in Even-Mansour, E_k(0) = P(k) ^ k uniquely identifies k
        expected_e0 = self.model.encrypt(0, self.active_mask)

        def verifier(cand_str: str) -> bool:
            cand = int(cand_str, 2)
            if cand == 0:
                return False
            # Check Even-Mansour encryption identity on 0
            if (self.model.P(cand) ^ cand) != expected_e0:
                return False
            # Verify periodicity property
            return self.model.periodic_function(0, self.active_mask) == self.model.periodic_function(cand, self.active_mask)

        # 2. Build and run Simon's algorithm
        simon = SimonsAlgorithm(oracle_qc, self.n)
        recovered_bitstr, counts, queries_used = simon.run(shots=shots, verifier_fn=verifier)

        if recovered_bitstr is None:
            return {
                "success": False,
                "error": "Failed to collect enough linearly independent equations",
                "queries_used": queries_used,
            }

        recovered_mask = int(recovered_bitstr, 2)

        # 3. Verify recovered mask against the active block mask
        mask_match = (recovered_mask == self.active_mask)

        # 4. Invert LFSR to recover root mask M_0
        recovered_root = recovered_mask
        for _ in range(self.step):
            recovered_root = self.model.lfsr_inv_step(recovered_root)

        root_match = (recovered_root == self.model.root_mask)

        # Quantum circuit statistics
        circuit_depth = simon.circuit.depth()
        qubit_count = simon.circuit.num_qubits

        return {
            "success": mask_match and root_match,
            "target_n_bits": self.n,
            "step_index": self.step,
            "true_active_mask": self.active_mask,
            "recovered_active_mask": recovered_mask,
            "active_mask_bitstring": recovered_bitstr,
            "mask_match": mask_match,
            "true_root_mask": self.model.root_mask,
            "recovered_root_mask": recovered_root,
            "root_match": root_match,
            "queries_used": queries_used,
            "total_shots": shots,
            "circuit_depth": circuit_depth,
            "qubit_count": qubit_count,
            "counts": counts,
        }
