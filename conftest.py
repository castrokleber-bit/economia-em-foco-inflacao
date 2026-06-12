import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: testes que fazem chamadas reais às APIs (IBGE, BCB).",
    )
