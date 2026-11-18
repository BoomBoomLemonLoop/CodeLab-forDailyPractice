"""Adiabatic closed constant-volume H2/air reactor; SI units throughout."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def run(temperature=1000.0, pressure=101325.0, phi=1.0, end_time=0.002, samples=2001):
    if not all(np.isfinite(v) and v > 0 for v in (temperature, pressure, phi, end_time)):
        raise ValueError("temperature, pressure, phi and end_time must be finite and positive")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 3:
        raise ValueError("samples must be an integer >= 3")
    try:
        import cantera as ct
    except ImportError as exc:
        raise RuntimeError('Cantera missing: python -m pip install -e ".[combustion]"') from exc
    gas = ct.Solution("h2o2.yaml")
    gas.TP = temperature, pressure
    gas.set_equivalence_ratio(phi, "H2", "O2:1, N2:3.76")
    reactor = ct.IdealGasReactor(gas, energy="on", volume=1.0, clone=False)
    network = ct.ReactorNet([reactor])
    network.rtol, network.atol = 1e-9, 1e-15
    initial_u, initial_mass = gas.int_energy_mass, reactor.mass
    times = np.linspace(0.0, end_time, samples)
    temperatures = np.empty(samples)
    temperatures[0] = temperature
    for i, time in enumerate(times[1:], 1):
        network.advance(float(time))
        temperatures[i] = reactor.T
    rate = np.gradient(temperatures, times)
    peak = int(np.argmax(rate))
    # A boundary maximum or negligible heat release is not a resolved ignition event.
    resolved = 0 < peak < samples - 1 and temperatures[-1] - temperature > 100
    phase = reactor.phase
    mechanism_path = next(
        Path(directory) / "h2o2.yaml"
        for directory in ct.get_data_directories()
        if (Path(directory) / "h2o2.yaml").is_file()
    )
    return {
        "cantera_version": ct.__version__,
        "mechanism": "h2o2.yaml",
        "mechanism_sha256": hashlib.sha256(mechanism_path.read_bytes()).hexdigest(),
        "temperature_K": temperature,
        "pressure_Pa": pressure,
        "phi": phi,
        "end_time_s": end_time,
        "samples": samples,
        "rtol": network.rtol,
        "atol": network.atol,
        "definition": "interior maximum of sampled dT/dt; temperature rise >100 K",
        "ignition_resolved": bool(resolved),
        "ignition_delay_s": float(times[peak]) if resolved else None,
        "final_temperature_K": float(reactor.T),
        "final_pressure_Pa": float(phase.P),
        "relative_energy_drift": float(
            abs(phase.int_energy_mass - initial_u) / max(abs(initial_u), 1.0)
        ),
        "relative_mass_drift": float(abs(reactor.mass - initial_mass) / initial_mass),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temperature", type=float, default=1000.0)
    parser.add_argument("--pressure", type=float, default=101325.0)
    parser.add_argument("--phi", type=float, default=1.0)
    parser.add_argument("--end-time", type=float, default=0.002)
    parser.add_argument("--samples", type=int, default=2001)
    args = parser.parse_args()
    try:
        print(json.dumps(run(**vars(args)), indent=2))
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
