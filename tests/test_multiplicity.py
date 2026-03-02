from __future__ import annotations

import pytest

from tkstatistics.stats.multiplicity import bonferroni_correction, holm_bonferroni_correction


# ---------------------------------------------------------------------------
# bonferroni_correction
# ---------------------------------------------------------------------------

def test_bonferroni_empty():
    assert bonferroni_correction([]) == []


def test_bonferroni_single_test_unchanged():
    result = bonferroni_correction([0.03])
    assert len(result) == 1
    assert result[0] == pytest.approx(0.03)


def test_bonferroni_order_preserved():
    p_values = [0.10, 0.01, 0.05]
    result = bonferroni_correction(p_values)
    # m=3; each multiplied by 3
    assert result[0] == pytest.approx(0.30)
    assert result[1] == pytest.approx(0.03)
    assert result[2] == pytest.approx(0.15)


def test_bonferroni_clamps_to_one():
    result = bonferroni_correction([0.5, 0.9])
    assert result[0] == pytest.approx(1.0)
    assert result[1] == pytest.approx(1.0)


def test_bonferroni_all_zeros():
    result = bonferroni_correction([0.0, 0.0, 0.0])
    assert result == [0.0, 0.0, 0.0]


def test_bonferroni_all_ones():
    result = bonferroni_correction([1.0, 1.0])
    assert result == [1.0, 1.0]


def test_bonferroni_formula():
    p_values = [0.01, 0.04, 0.20, 0.50]
    result = bonferroni_correction(p_values)
    m = 4
    for orig, adj in zip(p_values, result):
        assert adj == pytest.approx(min(orig * m, 1.0))


# ---------------------------------------------------------------------------
# holm_bonferroni_correction
# ---------------------------------------------------------------------------

def test_holm_empty():
    assert holm_bonferroni_correction([]) == []


def test_holm_single_test_unchanged():
    result = holm_bonferroni_correction([0.03])
    assert result == pytest.approx([0.03])


def test_holm_known_values():
    # m=4: [0.01, 0.04, 0.20, 0.50] → [0.04, 0.12, 0.40, 0.50]
    p_values = [0.01, 0.04, 0.20, 0.50]
    result = holm_bonferroni_correction(p_values)
    assert result == pytest.approx([0.04, 0.12, 0.40, 0.50])


def test_holm_order_preserved_non_sorted_input():
    # Input not in sorted order; output must correspond to original positions
    p_values = [0.50, 0.01, 0.20, 0.04]
    result = holm_bonferroni_correction(p_values)
    # After sorting: positions (1,0.01),(3,0.04),(2,0.20),(0,0.50)
    # rank0: factor=4, adj=max(0,4*0.01)=0.04 → 0.04
    # rank1: factor=3, adj=max(0.04,3*0.04)=0.12 → 0.12
    # rank2: factor=2, adj=max(0.12,2*0.20)=0.40 → 0.40
    # rank3: factor=1, adj=max(0.40,1*0.50)=0.50 → 0.50
    assert result[0] == pytest.approx(0.50)  # orig idx 0 -> rank3
    assert result[1] == pytest.approx(0.04)  # orig idx 1 -> rank0
    assert result[2] == pytest.approx(0.40)  # orig idx 2 -> rank2
    assert result[3] == pytest.approx(0.12)  # orig idx 3 -> rank1


def test_holm_cummax_clamping():
    # All large p-values should be clamped to 1.0
    result = holm_bonferroni_correction([0.9, 0.8, 0.7])
    assert all(v == pytest.approx(1.0) for v in result)


def test_holm_leq_bonferroni():
    # Holm is strictly more powerful: adjusted p ≤ Bonferroni adjusted p
    p_values = [0.01, 0.04, 0.10, 0.25, 0.50]
    holm = holm_bonferroni_correction(p_values)
    bonf = bonferroni_correction(p_values)
    for h, b in zip(holm, bonf):
        assert h <= b + 1e-12


def test_holm_all_zeros():
    result = holm_bonferroni_correction([0.0, 0.0, 0.0])
    assert result == [0.0, 0.0, 0.0]


def test_holm_all_ones():
    result = holm_bonferroni_correction([1.0, 1.0, 1.0])
    assert result == [1.0, 1.0, 1.0]


# Optional cross-check with statsmodels (skipped if absent)
try:
    from statsmodels.stats.multitest import multipletests as sm_multipletests

    _HAS_STATSMODELS = True
except ImportError:
    _HAS_STATSMODELS = False


@pytest.mark.skipif(not _HAS_STATSMODELS, reason="statsmodels not installed")
def test_holm_matches_statsmodels():
    p_values = [0.01, 0.04, 0.20, 0.50, 0.03, 0.08]
    our_result = holm_bonferroni_correction(p_values)
    _, sm_adjusted, _, _ = sm_multipletests(p_values, method="holm")
    for ours, theirs in zip(our_result, sm_adjusted):
        assert ours == pytest.approx(theirs, abs=1e-10)
