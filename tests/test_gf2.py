"""Unit tests for GF(2) linear solver."""

import pytest
from quantum.gf2_solver import GF2Solver


def test_gf2_rank_and_independence():
    """Verify rank calculation and linear independence detection."""
    solver = GF2Solver(3)
    assert solver.add_equation("100") is True
    assert solver.rank == 1

    # Redundant equation
    assert solver.add_equation("100") is False
    assert solver.rank == 1

    assert solver.add_equation("010") is True
    assert solver.rank == 2

    # Linear combination 100 ^ 010 = 110 (redundant)
    assert solver.add_equation("110") is False
    assert solver.rank == 2

    assert solver.add_equation("001") is True
    assert solver.rank == 3


def test_gf2_solve_known_period_3bits():
    """Verify solving for a known period s = '110'."""
    # Orthogonal vectors to s = 110: y such that y_0 ^ y_1 = 0
    # Possible non-zero vectors: '001', '110', '111'
    solver = GF2Solver(3)
    solver.add_equation("001")
    solver.add_equation("110")

    assert solver.is_solvable() is True
    s = solver.solve_as_bitstring()
    assert s == "110"
    assert solver.verify_solution([int(c) for c in s]) is True


def test_gf2_solve_known_period_4bits():
    """Verify solving for a 4-bit period s = '1011'."""
    # Period s = 1011 (indices 0, 2, 3)
    # y . s = y0 ^ y2 ^ y3 = 0
    solver = GF2Solver(4)
    solver.add_equation("0100")  # 0^0^0 = 0
    solver.add_equation("1010")  # 1^1^0 = 0
    solver.add_equation("1001")  # 1^0^1 = 0

    assert solver.is_solvable() is True
    s = solver.solve_as_bitstring()
    assert s == "1011"
    assert solver.verify_solution([int(c) for c in s]) is True


def test_gf2_zero_vector_handling():
    """Zero vector carries no information and should be ignored."""
    solver = GF2Solver(3)
    assert solver.add_equation("000") is False
    assert solver.rank == 0
