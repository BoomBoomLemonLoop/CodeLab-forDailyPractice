import pytest


@pytest.mark.parametrize(
    "kwargs",
    [{"temperature": -1}, {"phi": 0}, {"pressure": float("nan")}, {"samples": 2}, {"end_time": 0}],
)
def test_invalid_configuration(ignition, kwargs):
    with pytest.raises(ValueError):
        ignition.run(**kwargs)


@pytest.mark.integration
def test_ignition_conservation_and_sampling(ignition):
    pytest.importorskip("cantera")
    coarse = ignition.run(samples=2001)
    fine = ignition.run(samples=4001)
    assert coarse["ignition_resolved"] and fine["ignition_resolved"]
    assert coarse["ignition_delay_s"] == pytest.approx(fine["ignition_delay_s"], rel=0.01)
    assert fine["relative_energy_drift"] < 1e-6
    assert fine["relative_mass_drift"] < 1e-12
    assert fine["final_temperature_K"] > 1500


@pytest.mark.integration
def test_short_window_is_not_reported_as_ignition(ignition):
    pytest.importorskip("cantera")
    result = ignition.run(end_time=1e-8, samples=20)
    assert not result["ignition_resolved"]
    assert result["ignition_delay_s"] is None
