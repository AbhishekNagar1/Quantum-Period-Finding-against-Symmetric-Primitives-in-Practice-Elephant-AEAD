"""Unit tests for Simon's Quantum Algorithm using Qiskit Aer."""

import pytest
from quantum.oracle import CanonicalSimonOracle
from quantum.simon import SimonsAlgorithm, run_simon_for_period


@pytest.mark.parametrize("period", ["11", "01", "10"])
def test_simon_2qubit_periods(period):
    """Test Simon period recovery on all 2-bit non-zero periods."""
    recovered, is_correct, counts = run_simon_for_period(period, shots=512)
    assert is_correct is True
    assert recovered == period

    # Verify that all measured states y satisfy y . s = 0 mod 2
    for bitstr in counts.keys():
        norm_bitstr = bitstr[::-1]
        dot = sum(int(a) * int(b) for a, b in zip(norm_bitstr, period)) % 2
        assert dot == 0, f"Measured vector {norm_bitstr} not orthogonal to {period}!"


@pytest.mark.parametrize("period", ["101", "011", "110", "111"])
def test_simon_3qubit_periods(period):
    """Test Simon period recovery on various 3-bit periods."""
    recovered, is_correct, counts = run_simon_for_period(period, shots=1024)
    assert is_correct is True
    assert recovered == period


@pytest.mark.parametrize("period", ["1001", "1100", "0101", "1111"])
def test_simon_4qubit_periods(period):
    """Test Simon period recovery on 4-bit periods."""
    recovered, is_correct, counts = run_simon_for_period(period, shots=2048)
    assert is_correct is True
    assert recovered == period
