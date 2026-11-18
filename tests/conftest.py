"""Load case scripts without turning every research directory into a package."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_case(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def diffusion():
    return load_case("diffusion", "fundamentals/finite-volume-method/01-diffusion/diffusion.py")


@pytest.fixture
def ignition():
    return load_case("ignition", "simulations/cantera/zero-dimensional-ignition/ignition.py")
