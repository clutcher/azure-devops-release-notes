import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from azure_devops_client import AzureDevOpsClient, SYSTEM_ACCOUNT_PATTERNS
from models import WorkItem, Release


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
                    {'lastModifiedOn': '2025-11-06T11:39:14.667Z'}
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


def should_extract_prod_deployment_time_when_environment_exists(client):
    # Given release data with PROD environment
    release_data = {
        'environments': [
            {
                'name': 'DEV',
                'deploySteps': [
                    {'lastModifiedOn': '2025-11-05T11:39:14.667Z'}
                ]
            },
            {
                'name': 'PROD',
                'deploySteps': [
                    {'lastModifiedOn': '2025-11-06T11:39:14.667Z'}
                ]
            }
        ]
    }

    # When extracting production deployment time
    result = client._extract_prod_deployment_time(release_data)

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

    # When extracting production deployment time
    result = client._extract_prod_deployment_time(release_data)

    # Then should return None
    assert result is None


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
