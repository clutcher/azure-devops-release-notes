import pytest
from models import WorkItem, Release


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
