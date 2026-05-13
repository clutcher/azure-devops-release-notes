import pytest
from models import WorkItem, Release, E2ETestResults


def should_create_work_item_with_all_fields_when_provided():
    # Given all work item fields are provided
    work_item_id = 123
    title = "Test item"
    item_type = "Bug"
    state = "Done"
    iteration = "Sprint 1"

    # When creating a work item
    work_item = WorkItem(
        id=work_item_id,
        title=title,
        type=item_type,
        state=state,
        iteration_path=iteration
    )

    # Then all fields should be set correctly
    assert work_item.id == 123
    assert work_item.title == "Test item"
    assert work_item.type == "Bug"
    assert work_item.state == "Done"
    assert work_item.iteration_path == "Sprint 1"


def should_default_iteration_to_na_when_not_provided():
    # Given a work item without iteration path
    work_item_id = 123
    title = "Test item"
    item_type = "Bug"
    state = "Done"

    # When creating the work item
    work_item = WorkItem(
        id=work_item_id,
        title=title,
        type=item_type,
        state=state
    )

    # Then iteration path should default to N/A
    assert work_item.iteration_path == 'N/A'


def should_create_release_with_all_fields_when_provided():
    # Given all release fields are provided
    microservice = "test-service"
    version = "v1.0.0"
    deploy_time = "2025-11-06T11:39:14.667Z"
    release_id = "123"
    definition_id = "456"

    # When creating a release
    release = Release(
        microservice=microservice,
        version=version,
        prod_deploy_time=deploy_time,
        release_id=release_id,
        definition_id=definition_id
    )

    # Then all fields should be set correctly
    assert release.microservice == "test-service"
    assert release.version == "v1.0.0"
    assert release.prod_deploy_time == "2025-11-06T11:39:14.667Z"
    assert release.release_id == "123"
    assert release.definition_id == "456"


def should_create_release_with_defaults_when_optional_fields_omitted():
    # Given only required release fields are provided
    microservice = "test-service"
    version = "v1.0.0"

    # When creating a minimal release
    release = Release(
        microservice=microservice,
        version=version
    )

    # Then required fields should be set and optional fields should have defaults
    assert release.microservice == "test-service"
    assert release.version == "v1.0.0"
    assert release.prod_deploy_time is None
    assert release.release_id == ''
    assert release.definition_id == ''
    assert release.prod_approved_by is None
    assert release.prod_deployed_by is None


def should_create_release_with_approver_and_deployer_when_provided():
    # Given a release with production audit fields
    release = Release(
        microservice="test-service",
        version="v1.0.0",
        prod_approved_by="Alice Approver",
        prod_deployed_by="Bob Deployer"
    )

    # Then the audit fields should be set correctly
    assert release.prod_approved_by == "Alice Approver"
    assert release.prod_deployed_by == "Bob Deployer"


def should_create_e2e_test_results_with_all_fields_when_provided():
    # Given all E2E test results fields are provided
    build_id = "12345"
    passed = 42
    failed = 3
    skipped = 5
    total = 50
    pass_rate = 84.0
    build_url = "https://dev.azure.com/org/project/_build/results?buildId=12345"
    test_run_url = "https://dev.azure.com/org/project/_testManagement/runs?runId=999"

    # When creating E2E test results
    results = E2ETestResults(
        build_id=build_id,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
        pass_rate=pass_rate,
        build_url=build_url,
        test_run_url=test_run_url
    )

    # Then all fields should be set correctly
    assert results.build_id == "12345"
    assert results.passed == 42
    assert results.failed == 3
    assert results.skipped == 5
    assert results.total == 50
    assert results.pass_rate == 84.0
    assert results.build_url == build_url
    assert results.test_run_url == test_run_url


def should_create_e2e_test_results_with_optional_test_run_url_none():
    # Given E2E test results without test_run_url
    build_id = "12345"
    passed = 10
    failed = 0
    skipped = 0
    total = 10
    pass_rate = 100.0
    build_url = "https://dev.azure.com/org/project/_build/results?buildId=12345"

    # When creating E2E test results without test_run_url
    results = E2ETestResults(
        build_id=build_id,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
        pass_rate=pass_rate,
        build_url=build_url
    )

    # Then test_run_url should be None
    assert results.test_run_url is None
    assert results.passed == 10
    assert results.pass_rate == 100.0
