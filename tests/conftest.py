import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from models import WorkItem, Release


@pytest.fixture
def sample_work_items():
    return [
        WorkItem(id=1, title="Fix login bug", type="Bug", state="Done", iteration_path="Sprint 1"),
        WorkItem(id=2, title="Add user dashboard", type="Feature", state="Done", iteration_path="Sprint 1"),
        WorkItem(id=3, title="Update API docs", type="Task", state="Done", iteration_path="Sprint 2"),
        WorkItem(id=4, title="Implement authentication", type="User Story", state="Done", iteration_path="Sprint 1"),
    ]


@pytest.fixture
def sample_releases():
    return [
        Release(
            microservice="auth-service",
            version="v1.2.3",
            prod_deploy_time="2025-11-06T11:39:14.667Z",
            release_id="123",
            definition_id="456"
        ),
        Release(
            microservice="api-gateway",
            version="v2.0.1",
            prod_deploy_time="2025-11-06T12:00:00.000Z",
            release_id="124",
            definition_id="457"
        ),
    ]


@pytest.fixture
def sample_contributors():
    return {"Alice Developer", "Bob Engineer", "Charlie Tester"}


@pytest.fixture
def organization_url():
    return "https://dev.azure.com/testorg"


@pytest.fixture
def project_name():
    return "TestProject"


@pytest.fixture
def pat_token():
    return "test_pat_token_123"
