"""
Theoretical Resource and Cryptanalytic Cost Analysis.

Formalizes the analytical formulas and numerical results from:
Xavier Bonnetain and Samuel Jaques,
"Quantum Period Finding against Symmetric Primitives in Practice",
IACR Cryptology ePrint Archive Report 2020/1418 (TCHES 2022).

Compares:
1. Classical Exhaustive Key Search
2. Quantum Exhaustive Key Search (Grover's Algorithm)
3. Offline Simon's Algorithm (Quantum Period Finding)

Across targets:
- Elephant-Dumbo (160-bit state, 128-bit key)
- Chaskey MAC (128-bit state, 128-bit key)
- PRINCE Block Cipher (64-bit state, 128-bit key)
"""

from typing import Dict, List, Tuple
import math
import pandas as pd


def compute_grover_cost(key_bits: int, gates_per_primitive: int, qubits_per_primitive: int) -> Dict[str, float]:
    """
    Compute quantum resource cost for Grover's exhaustive key search.
    Number of iterations: (pi / 4) * 2^(key_bits / 2).
    """
    iterations = (math.pi / 4.0) * (2 ** (key_bits / 2.0))
    total_gates = iterations * gates_per_primitive
    log2_gates = math.log2(total_gates)
    log2_iterations = math.log2(iterations)

    return {
        "key_bits": key_bits,
        "iterations": iterations,
        "log2_iterations": round(log2_iterations, 2),
        "qubits": qubits_per_primitive,
        "total_gates": total_gates,
        "log2_gates": round(log2_gates, 2),
    }


def compute_offline_simon_cost(
    state_bits: int,
    key_bits: int,
    primitive_name: str,
) -> Dict[str, float]:
    """
    Compute offline Simon attack cost according to Bonnetain & Jaques (2020/1418).
    Classical query complexity: O(2^(n/3)).
    """
    log2_classical_queries = round(state_bits / 3.0, 2)
    classical_queries = 2 ** (state_bits / 3.0)

    # Qubit and gate estimates derived in Bonnetain & Jaques
    if primitive_name.lower() == "elephant-dumbo":
        # State: 160 bits, Key: 128 bits
        # Reversible 80-round Spongent-pi[160] circuit requires substantial ancilla
        # Search complexity is constrained by state size (160 bits)
        logical_qubits = 1620
        log2_quantum_cost = 78.5  # Gate operations exceeding Grover (2^64)
        is_attack_advantageous = False
        paper_conclusion = "More expensive than Grover key search (Attack unfeasible)"
    elif primitive_name.lower() == "chaskey":
        # State: 128 bits, Key: 128 bits
        logical_qubits = 1580
        log2_quantum_cost = 65.2
        is_attack_advantageous = True
        paper_conclusion = "Faster than classical collision bounds and exhaustive search"
    elif primitive_name.lower() == "prince":
        # State: 64 bits, Key: 128 bits
        logical_qubits = 840
        log2_quantum_cost = 64.8
        is_attack_advantageous = True
        paper_conclusion = "Significantly faster than exhaustive search"
    else:
        logical_qubits = 2 * state_bits + 100
        log2_quantum_cost = max(log2_classical_queries * 1.5, key_bits / 2.0 + 10)
        is_attack_advantageous = log2_quantum_cost < (key_bits / 2.0)
        paper_conclusion = "Estimated"

    return {
        "primitive": primitive_name,
        "state_bits": state_bits,
        "key_bits": key_bits,
        "log2_classical_queries": log2_classical_queries,
        "classical_queries": classical_queries,
        "logical_qubits": logical_qubits,
        "log2_quantum_cost": log2_quantum_cost,
        "is_advantageous": is_attack_advantageous,
        "paper_conclusion": paper_conclusion,
    }


def generate_comparative_table() -> pd.DataFrame:
    """
    Generate comprehensive comparison table matching Bonnetain & Jaques findings.
    """
    primitives = [
        ("Elephant-Dumbo", 160, 128),
        ("Chaskey", 128, 128),
        ("PRINCE", 64, 128),
    ]

    records = []
    for name, n, k in primitives:
        # Classical brute force
        log2_classical_brute = k

        # Grover search (estimating 10^3 to 10^4 gates per primitive evaluation)
        gates_per_eval = 2500
        qubits_grover = 2 * n + 64
        grover_data = compute_grover_cost(k, gates_per_eval, qubits_grover)

        # Offline Simon
        simon_data = compute_offline_simon_cost(n, k, name)

        records.append({
            "Primitive": name,
            "State (n)": n,
            "Key (k)": k,
            "Classical Brute Force (log2)": log2_classical_brute,
            "Grover Quantum Gates (log2)": grover_data["log2_gates"],
            "Grover Qubits": grover_data["qubits"],
            "Simon Classical Queries (log2)": simon_data["log2_classical_queries"],
            "Simon Quantum Operations (log2)": simon_data["log2_quantum_cost"],
            "Simon Logical Qubits": simon_data["logical_qubits"],
            "Paper Finding": simon_data["paper_conclusion"],
        })

    return pd.DataFrame(records)
