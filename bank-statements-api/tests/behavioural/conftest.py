import json
import os
import random

import httpx
import pytest

SUITE = os.path.dirname(os.path.abspath(__file__))

IDS = {}
FAILED = []
COUNTS = {"passed": 0, "failed": 0, "skipped": 0}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "behaviour(id): the stable dotted id this test is known by outside the suite",
    )


def pytest_collection_modifyitems(config, items):
    unmarked = []
    for item in items:
        if not str(item.path).startswith(SUITE):
            continue
        marker = item.get_closest_marker("behaviour")
        if marker is None or not marker.args:
            unmarked.append(item.nodeid)
            continue
        IDS[item.nodeid] = marker.args[0]
    if unmarked:
        raise pytest.UsageError(
            "every behavioural test needs @pytest.mark.behaviour(<dotted id>), so a caller "
            "can map a red test back to a decision even after the test is renamed. Missing on:\n  " + "\n  ".join(unmarked)
        )


def pytest_runtest_logreport(report):
    if report.when == "call" and report.passed:
        COUNTS["passed"] += 1
    elif report.skipped and report.when == "setup":
        COUNTS["skipped"] += 1
    elif report.failed:
        identifier = IDS.get(report.nodeid, report.nodeid)
        if identifier not in FAILED:
            FAILED.append(identifier)
            COUNTS["failed"] += 1


def pytest_sessionfinish(session):
    destination = os.environ.get("BSAI_API_RESULT_JSON")
    if not destination:
        return
    with open(destination, "w") as handle:
        json.dump(
            {
                "summary": {"total": sum(COUNTS.values()), **COUNTS},
                "failed": FAILED,
            },
            handle,
        )


@pytest.fixture(scope="session")
def base_url():
    port = os.environ.get("BSAI_API_PORT", "8020")
    return f"http://127.0.0.1:{port}/api/v1"


@pytest.fixture(scope="session")
def seed():
    return os.environ.get("BSAI_API_SEED", "0")


@pytest.fixture
def unique(seed, request):
    generator = random.Random(f"{seed}:{request.node.nodeid}")

    def name(prefix):
        return f"{prefix}-{generator.randrange(16 ** 12):012x}"

    return name


@pytest.fixture(scope="session")
def client(base_url):
    with httpx.Client(base_url=base_url, timeout=30.0) as session:
        response = session.post("/auth/test-login")
        assert response.status_code == 200, f"test-login failed: {response.status_code} {response.text}"
        yield session
