def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: browser tests against the running docker compose stack")
