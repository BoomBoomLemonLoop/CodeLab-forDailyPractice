import numpy as np
import pytest


def test_analytical_solution_and_order(diffusion):
    errors = [diffusion.report(n)["l2_rms"] for n in (20, 40, 80)]
    assert errors[-1] < 1e-4
    orders = np.log2(np.array(errors[:-1]) / errors[1:])
    assert np.all((orders > 1.95) & (orders < 2.05))


def test_conservation_and_symmetry(diffusion):
    n = 40
    x, u = diffusion.solve(n)
    h = 1 / n
    assert np.allclose(u, u[::-1], atol=1e-13)
    assert np.all(u > 0)
    outward_flux = 2 * (u[0] + u[-1]) / h
    source_integral = np.sum(np.pi**2 * np.sin(np.pi * x)) * h
    assert outward_flux == pytest.approx(source_integral, rel=1e-12)


@pytest.mark.parametrize("cells", [0, 1, -1, 2.5, True, 2001])
def test_invalid_mesh(diffusion, cells):
    with pytest.raises(ValueError):
        diffusion.solve(cells)
