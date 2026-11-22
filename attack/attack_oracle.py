"""
Elephant Attack Quantum Oracle Synthesizer.

Builds the reversible quantum circuit evaluating the periodic function:
    f(x) = E_k(x) ^ P(x) = P(x ^ k) ^ k ^ P(x)
where E_k is the reduced Elephant Even-Mansour encryption, P is the
Spongent-derived permutation, and k is the secret mask.

The circuit acts on:
    qr_in: n qubits (|x>)
    qr_out: n qubits (|y>)
mapping:
    |x>|y> -> |x>|y ^ f(x)>
"""

from typing import Union
from qiskit import QuantumCircuit, QuantumRegister
from quantum.oracle import CustomFunctionOracle
from attack.reduced_elephant import ReducedElephant4Bit, ReducedElephant8Bit


def build_elephant_attack_oracle(
    model: Union[ReducedElephant4Bit, ReducedElephant8Bit],
    mask: int = None,
) -> QuantumCircuit:
    """
    Construct the quantum oracle circuit for the reduced Elephant periodic function.
    """
    n = model.n
    k = model.secret_mask if mask is None else mask

    # Verify periodicity classical identity: f(x ^ k) == f(x) for all x in 2^n
    for x in range(2**n):
        f_x = model.periodic_function(x, k)
        f_xk = model.periodic_function(x ^ k, k)
        assert f_x == f_xk, f"Mathematical periodicity broken at x={x}: f(x)={f_x} != f(x^k)={f_xk}"

    # Build reversible quantum circuit
    custom_oracle = CustomFunctionOracle(n, lambda x: model.periodic_function(x, k))
    circuit = custom_oracle.to_circuit()
    circuit.name = f"ElephantOracle_n={n}_mask={bin(k)}"
    return circuit
