import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from azure_devops_client import AzureDevOpsClient, SYSTEM_ACCOUNT_PATTERNS
from models import WorkItem, Release, E2ETestResults


@pytest.fixture
def client(organization_url, project_name, pat_token):
    return AzureDevOpsClient(organization_url, project_name, pat_token)


def should_initialize_client_with_auth_header_when_created(client, organization_url, project_name, pat_token):
    # Given a client is created with credentials
    # When checking client properties
    # Then all properties should be set correctly
    assert client.organization_url == organization_url
    assert client.project == project_name
    assert client.pat == pat_token
    assert client.auth_header.startswith('Basic ')


def should_create_basic_auth_header_when_requested(client):
    # Given a client with PAT token
    # When creating auth header
    auth_header = client._create_auth_header()

    # Then should return valid Basic auth header
    assert auth_header.startswith('Basic ')
    assert len(auth_header) > 10


def should_return_work_item_ids_when_query_matches_release(client):
    # Given Azure DevOps API returns matching work items
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'workItems': [{'id': 1}, {'id': 2}, {'id': 3}]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When querying for work item IDs
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.query_work_item_ids("2025.006")

    # Then should return list of work item IDs
    assert result == [1, 2, 3]


def should_return_empty_list_when_no_work_items_match_release(client):
    # Given Azure DevOps API returns no work items
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'workItems': []}).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When querying for work item IDs
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.query_work_item_ids("2025.006")

    # Then should return empty list
    assert result == []


def should_return_empty_list_when_work_item_ids_are_empty(client):
    # Given an empty list of work item IDs
    empty_ids = []

    # When getting work item details
    result = client.get_work_item_details(empty_ids)

    # Then should return empty list without API call
    assert result == []


def should_return_work_items_when_details_are_fetched(client):
    # Given Azure DevOps API returns work item details (with $expand=relations format)
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'value': [
            {
                'id': 1,  # ID is at top level when using $expand
                'fields': {
                    'System.Title': 'Test Bug',
                    'System.WorkItemType': 'Bug',
                    'System.State': 'Done',
                    'System.IterationPath': 'Sprint 1'
                }
            }
        ]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When getting work item details
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_work_item_details([1])

    # Then should return list of WorkItem objects
    assert len(result) == 1
    assert isinstance(result[0], WorkItem)
    assert result[0].id == 1
    assert result[0].title == 'Test Bug'
    assert result[0].type == 'Bug'


def should_identify_system_account_when_pattern_matches(client):
    # Given display names with system account patterns
    # When checking if they are system accounts
    # Then should correctly identify them
    assert client._is_system_account('Microsoft.VisualStudio.Services.TFS') == True
    assert client._is_system_account('Project Collection Build Service') == True
    assert client._is_system_account('Regular User') == False
    assert client._is_system_account('Alice <alice@example.com>') == True


def should_extract_contributor_name_when_valid_user(client):
    # Given update with valid contributor
    update = {
        'revisedBy': {
            'displayName': 'Alice Developer'
        }
    }

    # When extracting contributor
    result = client._extract_contributor(update)

    # Then should return contributor name
    assert result == 'Alice Developer'


def should_return_none_when_contributor_is_system_account(client):
    # Given update with system account
    update = {
        'revisedBy': {
            'displayName': 'Microsoft.VisualStudio.Services.TFS'
        }
    }

    # When extracting contributor
    result = client._extract_contributor(update)

    # Then should return None
    assert result is None


def should_return_empty_set_when_no_work_items_for_contributors(client):
    # Given empty list of work item IDs
    empty_ids = []

    # When getting contributors
    result = client.get_work_item_contributors(empty_ids)

    # Then should return empty set
    assert result == set()


def should_convert_to_vsrm_url_when_using_dev_azure(client):
    # Given organization URL with dev.azure.com
    client.organization_url = "https://dev.azure.com/myorg"

    # When getting VSRM URL
    result = client._get_vsrm_url()

    # Then should convert to vsrm.dev.azure.com
    assert result == "https://vsrm.dev.azure.com/myorg"


def should_return_same_url_when_not_dev_azure(client):
    # Given custom server URL
    client.organization_url = "https://custom.server.com"

    # When getting VSRM URL
    result = client._get_vsrm_url()

    # Then should return same URL
    assert result == "https://custom.server.com"


def should_parse_classic_release_with_all_fields_when_provided(client):
    # Given release data from Azure DevOps API
    release_data = {
        'releaseDefinition': {
            'name': 'auth-service',
            'id': '456'
        },
        'name': 'Release-123',
        'id': '789',
        'environments': [
            {
                'name': 'PROD',
                'deploySteps': [
                    {
                        'lastModifiedOn': '2025-11-06T11:39:14.667Z',
                        'requestedBy': {'displayName': 'Bob Deployer'}
                    }
                ],
                'preDeployApprovals': [
                    {
                        'status': 'approved',
                        'approvedBy': {'displayName': 'Alice Approver'}
                    }
                ]
            }
        ]
    }

    # When parsing classic release
    result = client._parse_classic_release(release_data)

    # Then should return Release object with all fields
    assert isinstance(result, Release)
    assert result.microservice == 'auth-service'
    assert result.version == 'Release-123'
    assert result.release_id == '789'
    assert result.definition_id == '456'
    assert result.prod_deploy_time == '2025-11-06T11:39:14.667Z'
    assert result.prod_approved_by == 'Alice Approver'
    assert result.prod_deployed_by == 'Bob Deployer'


def should_extract_prod_deployment_time_when_environment_exists(client):
    # Given a PROD environment with deploy steps
    prod_environment = {
        'name': 'PROD',
        'deploySteps': [
            {'lastModifiedOn': '2025-11-06T11:39:14.667Z'}
        ]
    }

    # When extracting production deployment time
    result = client._extract_prod_deployment_time(prod_environment)

    # Then should return PROD environment deployment time
    assert result == '2025-11-06T11:39:14.667Z'


def should_return_none_when_prod_environment_not_found(client):
    # Given release data without PROD environment
    release_data = {
        'environments': [
            {
                'name': 'DEV',
                'deploySteps': [
                    {'lastModifiedOn': '2025-11-05T11:39:14.667Z'}
                ]
            }
        ]
    }

    # When finding the prod environment
    prod_environment = client._find_prod_environment(release_data)

    # Then no environment should be found
    assert prod_environment is None
    assert client._extract_prod_deployment_time(prod_environment) is None
    assert client._extract_release_approver(release_data, prod_environment) is None
    assert client._extract_release_deployer(prod_environment) is None


def should_find_prod_environment_when_present(client):
    # Given release data with both DEV and PROD environments
    release_data = {
        'environments': [
            {'name': 'DEV'},
            {'name': 'PROD', 'deploySteps': [{'lastModifiedOn': '2025-11-06T11:39:14.667Z'}]}
        ]
    }

    # When finding the prod environment
    prod_environment = client._find_prod_environment(release_data)

    # Then should return the PROD environment
    assert prod_environment is not None
    assert prod_environment.get('name') == 'PROD'


def should_extract_manual_prod_approver_when_human_approval_present(client):
    # Given a PROD environment with a human approval
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'preDeployApprovals': [
                    {'status': 'approved', 'approvedBy': {'displayName': 'Alice Approver'}}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release approver
    result = client._extract_release_approver(release_data, prod_environment)

    # Then should return the human approver
    assert result == 'Alice Approver'


def should_use_latest_prod_approver_when_multiple_approvals_exist(client):
    # Given multiple approved approvals on PROD
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'preDeployApprovals': [
                    {'status': 'approved', 'approvedBy': {'displayName': 'First Approver'}},
                    {'status': 'approved', 'approvedBy': {'displayName': 'Latest Approver'}}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release approver
    result = client._extract_release_approver(release_data, prod_environment)

    # Then should return the most recent approver
    assert result == 'Latest Approver'


def should_skip_pending_prod_approvals_when_extracting_approver(client):
    # Given pending and approved approvals on PROD
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'preDeployApprovals': [
                    {'status': 'approved', 'approvedBy': {'displayName': 'Alice Approver'}},
                    {'status': 'pending', 'approvedBy': {'displayName': 'Pending Person'}}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release approver
    result = client._extract_release_approver(release_data, prod_environment)

    # Then should ignore pending entries and return the approved one
    assert result == 'Alice Approver'


def should_fall_back_to_comment_when_prod_approval_is_automated(client):
    # Given an automated bot approval on PROD with a human name embedded in another env's comments
    release_data = {
        'environments': [
            {
                'name': 'PROMOTE',
                'preDeployApprovals': [
                    {
                        'status': 'approved',
                        'isAutomated': False,
                        'approvedBy': {'displayName': 'Project Collection Build Service (Org)'},
                        'comments': 'Approved by Otoniel Cajigas via approval-release pipeline for release 2026.014'
                    }
                ]
            },
            {
                'name': 'PROD',
                'preDeployApprovals': [
                    {'status': 'approved', 'isAutomated': True, 'comments': ''}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release approver
    result = client._extract_release_approver(release_data, prod_environment)

    # Then should return the human name extracted from PROMOTE comments
    assert result == 'Otoniel Cajigas'


def should_parse_approver_name_from_comment_when_pattern_matches(client):
    # Given an approval comment with the standard pipeline message
    comment = 'Approved by Nagesh Panyam via approval-release pipeline for release 2026.015'

    # When parsing the comment
    result = client._parse_approver_comment(comment)

    # Then should return the approver name
    assert result == 'Nagesh Panyam'


def should_return_none_when_comment_does_not_match_pattern(client):
    # Given a comment without the expected pattern
    comment = 'Auto-approved by configuration'

    # When parsing the comment
    result = client._parse_approver_comment(comment)

    # Then should return None
    assert result is None


def should_return_none_when_comment_is_empty(client):
    # Given an empty/missing comment
    assert client._parse_approver_comment(None) is None
    assert client._parse_approver_comment('') is None


def should_extract_prod_deployer_when_human_triggered_prod_deploy(client):
    # Given a PROD deploy step triggered by a human
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'deploySteps': [{'requestedBy': {'displayName': 'Bob Deployer'}}]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release deployer
    result = client._extract_release_deployer(prod_environment)

    # Then should return the human deployer
    assert result == 'Bob Deployer'


def should_return_none_when_prod_deploy_triggered_by_system_account(client):
    # Given a PROD deploy step triggered only by a system account
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'deploySteps': [
                    {'requestedBy': {'displayName': 'Project Collection Build Service'}}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release deployer
    result = client._extract_release_deployer(prod_environment)

    # Then should return None (no human deployer is recorded)
    assert result is None


def should_return_latest_prod_deployer_when_multiple_steps_exist(client):
    # Given multiple deploy steps on PROD
    release_data = {
        'environments': [
            {
                'name': 'PROD',
                'deploySteps': [
                    {'requestedBy': {'displayName': 'First Deployer'}},
                    {'requestedBy': {'displayName': 'Latest Deployer'}}
                ]
            }
        ]
    }
    prod_environment = client._find_prod_environment(release_data)

    # When extracting the release deployer
    result = client._extract_release_deployer(prod_environment)

    # Then should return the most recent deployer
    assert result == 'Latest Deployer'


def should_return_none_when_notes_field_is_missing(client):
    # Given work item API response without notes field
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'value': [
            {
                'id': 1,
                'fields': {
                    'System.Title': 'Test Bug',
                    'System.WorkItemType': 'Bug',
                    'System.State': 'Done',
                    'System.IterationPath': 'Sprint 1'
                }
            }
        ]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When getting work item details
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_work_item_details([1])

    # Then notes should be None
    assert result[0].notes is None


def should_strip_whitespace_from_notes_when_present(client):
    # Given work item with notes containing whitespace
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'value': [
            {
                'id': 1,
                'fields': {
                    'System.Title': 'Test Bug',
                    'System.WorkItemType': 'Bug',
                    'System.State': 'Done',
                    'System.IterationPath': 'Sprint 1',
                    'Custom.Notes': '  Deploy to production first  '
                }
            }
        ]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When getting work item details
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_work_item_details([1])

    # Then whitespace should be stripped
    assert result[0].notes == 'Deploy to production first'


def should_preserve_html_in_notes_when_present(client):
    # Given work item with HTML in notes
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'value': [
            {
                'id': 1,
                'fields': {
                    'System.Title': 'Test Bug',
                    'System.WorkItemType': 'Bug',
                    'System.State': 'Done',
                    'System.IterationPath': 'Sprint 1',
                    'Custom.Notes': '<ul><li>Deploy to production first</li></ul>'
                }
            }
        ]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When getting work item details
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_work_item_details([1])

    # Then HTML should be preserved for markdown generator
    assert result[0].notes == '<ul><li>Deploy to production first</li></ul>'


def should_return_none_when_notes_are_only_whitespace(client):
    # Given work item with only whitespace in notes
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({
        'value': [
            {
                'id': 1,
                'fields': {
                    'System.Title': 'Test Bug',
                    'System.WorkItemType': 'Bug',
                    'System.State': 'Done',
                    'System.IterationPath': 'Sprint 1',
                    'Custom.Notes': '    '
                }
            }
        ]
    }).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When getting work item details
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_work_item_details([1])

    # Then notes should be None
    assert result[0].notes is None


def should_extract_parent_id_when_hierarchy_reverse_relation_exists(client):
    # Given relations array with parent link
    relations = [
        {
            'rel': 'System.LinkTypes.Hierarchy-Reverse',
            'url': 'https://dev.azure.com/org/project/_apis/wit/workitems/12345',
            'attributes': {'name': 'Parent'}
        }
    ]

    # When extracting parent ID
    result = client._extract_parent_id(relations)

    # Then should return parent ID
    assert result == 12345


def should_return_none_when_no_parent_relation_exists(client):
    # Given relations array without parent link
    relations = [
        {
            'rel': 'System.LinkTypes.Related',
            'url': 'https://dev.azure.com/org/project/_apis/wit/workitems/67890'
        }
    ]

    # When extracting parent ID
    result = client._extract_parent_id(relations)

    # Then should return None
    assert result is None


def should_return_none_when_relations_is_empty(client):
    # Given empty relations array
    relations = []

    # When extracting parent ID
    result = client._extract_parent_id(relations)

    # Then should return None
    assert result is None


def should_return_none_when_relations_is_none(client):
    # Given None relations
    relations = None

    # When extracting parent ID
    result = client._extract_parent_id(relations)

    # Then should return None
    assert result is None


def should_return_e2e_test_results_when_test_run_exists(client):
    # Given Azure DevOps API returns test runs for build
    mock_test_runs_response = Mock()
    mock_test_runs_response.read.return_value = json.dumps({
        'value': [{'id': 999}]
    }).encode('utf-8')
    mock_test_runs_response.__enter__ = Mock(return_value=mock_test_runs_response)
    mock_test_runs_response.__exit__ = Mock(return_value=False)

    mock_test_run_response = Mock()
    mock_test_run_response.read.return_value = json.dumps({
        'passedTests': 42,
        'unanalyzedTests': 3,
        'totalTests': 50,
        'notApplicableTests': 5
    }).encode('utf-8')
    mock_test_run_response.__enter__ = Mock(return_value=mock_test_run_response)
    mock_test_run_response.__exit__ = Mock(return_value=False)

    # When fetching E2E test results
    with patch('urllib.request.urlopen', side_effect=[mock_test_runs_response, mock_test_run_response]):
        result = client.get_e2e_test_results("12345")

    # Then should return E2ETestResults with correct values
    assert isinstance(result, E2ETestResults)
    assert result.build_id == "12345"
    assert result.passed == 42
    assert result.failed == 3
    assert result.skipped == 5
    assert result.total == 50
    assert result.pass_rate == 84.0
    assert "12345" in result.build_url
    assert "999" in result.test_run_url


def should_return_none_when_no_test_runs_found(client):
    # Given Azure DevOps API returns empty test runs
    mock_response = Mock()
    mock_response.read.return_value = json.dumps({'value': []}).encode('utf-8')
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    # When fetching E2E test results
    with patch('urllib.request.urlopen', return_value=mock_response):
        result = client.get_e2e_test_results("12345")

    # Then should return None
    assert result is None


def should_return_none_when_api_error_occurs(client):
    # Given Azure DevOps API returns an error
    import urllib.error

    # When fetching E2E test results and API fails
    with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError(None, 404, 'Not Found', {}, None)):
        result = client.get_e2e_test_results("12345")

    # Then should return None gracefully
    assert result is None


def should_calculate_zero_pass_rate_when_total_is_zero(client):
    # Given Azure DevOps API returns test run with zero tests
    mock_test_runs_response = Mock()
    mock_test_runs_response.read.return_value = json.dumps({
        'value': [{'id': 999}]
    }).encode('utf-8')
    mock_test_runs_response.__enter__ = Mock(return_value=mock_test_runs_response)
    mock_test_runs_response.__exit__ = Mock(return_value=False)

    mock_test_run_response = Mock()
    mock_test_run_response.read.return_value = json.dumps({
        'passedTests': 0,
        'unanalyzedTests': 0,
        'totalTests': 0,
        'notApplicableTests': 0
    }).encode('utf-8')
    mock_test_run_response.__enter__ = Mock(return_value=mock_test_run_response)
    mock_test_run_response.__exit__ = Mock(return_value=False)

    # When fetching E2E test results
    with patch('urllib.request.urlopen', side_effect=[mock_test_runs_response, mock_test_run_response]):
        result = client.get_e2e_test_results("12345")

    # Then pass rate should be 0 (no division by zero error)
    assert result.pass_rate == 0
