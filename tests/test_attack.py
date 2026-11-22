"""Unit and integration tests for the Elephant Quantum Attack module."""

import pytest
from attack.reduced_elephant import ReducedElephant4Bit, ReducedElephant8Bit
from attack.attack_oracle import build_elephant_attack_oracle
from attack.recovery_pipeline import ElephantAttackPipeline


def test_reduced_elephant_4bit_periodicity():
    """Verify that f(x ^ k) == f(x) for all 4-bit masks and all inputs."""
    for mask in range(1, 16):
        model = ReducedElephant4Bit(secret_mask=mask)
        for x in range(16):
            assert model.periodic_function(x) == model.periodic_function(x ^ mask)


def test_reduced_elephant_8bit_periodicity():
    """Verify that f(x ^ k) == f(x) for 8-bit model."""
    for mask in [0x15, 0xA3, 0x5C, 0xF0]:
        model = ReducedElephant8Bit(secret_mask=mask)
        for x in range(256):
            assert model.periodic_function(x) == model.periodic_function(x ^ mask)


def test_reduced_lfsr_invertibility():
    """Verify reduced LFSR roundtrips for 4-bit and 8-bit models."""
    m4 = ReducedElephant4Bit(secret_mask=0b1011)
    for mask in range(1, 16):
        fwd = m4.lfsr_step(mask)
        rev = m4.lfsr_inv_step(fwd)
        assert rev == mask

    m8 = ReducedElephant8Bit(secret_mask=0b11001010)
    for mask in range(1, 256):
        fwd = m8.lfsr_step(mask)
        rev = m8.lfsr_inv_step(fwd)
        assert rev == mask


@pytest.mark.parametrize("secret_mask", [0b0101, 0b1011, 0b1110, 0b0011])
def test_end_to_end_elephant_attack_4bit(secret_mask):
    """Execute complete quantum attack on 4-bit Elephant model."""
    model = ReducedElephant4Bit(secret_mask=secret_mask)
    pipeline = ElephantAttackPipeline(model, step_index=2)
    result = pipeline.execute_attack(shots=2048)

    assert result["success"] is True
    assert result["mask_match"] is True
    assert result["root_match"] is True
    assert result["recovered_root_mask"] == secret_mask


def test_end_to_end_elephant_attack_8bit():
    """Execute complete quantum attack on 8-bit Elephant model."""
    secret_mask = 0b10101100  # 0xAC
    model = ReducedElephant8Bit(secret_mask=secret_mask)
    pipeline = ElephantAttackPipeline(model, step_index=1)
    result = pipeline.execute_attack(shots=4096)

    assert result["success"] is True
    assert result["mask_match"] is True
    assert result["root_match"] is True
    assert result["recovered_root_mask"] == secret_mask
