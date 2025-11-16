import pytest
from config import AzureDevOpsConfig


def should_create_config_with_defaults_when_only_required_fields_provided(organization_url, project_name, pat_token):
    # Given required configuration fields
    org_url = organization_url
    project = project_name
    pat = pat_token

    # When creating config with only required fields
    config = AzureDevOpsConfig(
        organization_url=org_url,
        project=project,
        pat=pat
    )

    # Then config should be created with default values
    assert config.organization_url == organization_url
    assert config.project == project_name
    assert config.pat == pat_token
    assert config.release_field == 'Custom.Release'
    assert config.production_environment == 'PROD'


def should_use_custom_field_values_when_provided():
    # Given custom field configuration
    org_url = "https://dev.azure.com/org"
    project = "MyProject"
    pat = "token"
    custom_release_field = "Custom.Version"
    custom_prod_env = "Production"

    # When creating config with custom fields
    config = AzureDevOpsConfig(
        organization_url=org_url,
        project=project,
        pat=pat,
        release_field=custom_release_field,
        production_environment=custom_prod_env
    )

    # Then custom values should be used
    assert config.release_field == "Custom.Version"
    assert config.production_environment == "Production"


def should_strip_trailing_slash_from_url_when_present():
    # Given organization URL with trailing slash
    org_url_with_slash = "https://dev.azure.com/org/"
    project = "MyProject"
    pat = "token"

    # When creating config
    config = AzureDevOpsConfig(
        organization_url=org_url_with_slash,
        project=project,
        pat=pat
    )

    # Then trailing slash should be removed
    assert config.organization_url == "https://dev.azure.com/org"


def should_raise_error_when_organization_url_is_empty():
    # Given empty organization URL
    empty_url = ""
    project = "MyProject"
    pat = "token"

    # When creating config with empty organization URL
    # Then should raise ValueError
    with pytest.raises(ValueError, match="organization_url, project, and PAT token are required"):
        AzureDevOpsConfig(
            organization_url=empty_url,
            project=project,
            pat=pat
        )


def should_raise_error_when_project_is_empty():
    # Given empty project name
    org_url = "https://dev.azure.com/org"
    empty_project = ""
    pat = "token"

    # When creating config with empty project
    # Then should raise ValueError
    with pytest.raises(ValueError, match="organization_url, project, and PAT token are required"):
        AzureDevOpsConfig(
            organization_url=org_url,
            project=empty_project,
            pat=pat
        )


def should_raise_error_when_pat_is_empty():
    # Given empty PAT token
    org_url = "https://dev.azure.com/org"
    project = "MyProject"
    empty_pat = ""

    # When creating config with empty PAT
    # Then should raise ValueError
    with pytest.raises(ValueError, match="organization_url, project, and PAT token are required"):
        AzureDevOpsConfig(
            organization_url=org_url,
            project=project,
            pat=empty_pat
        )


def should_use_custom_notes_field_when_provided():
    # Given custom notes field configuration
    org_url = "https://dev.azure.com/org"
    project = "MyProject"
    pat = "token"
    custom_notes_field = "Custom.DeploymentInstructions"

    # When creating config with custom notes field
    config = AzureDevOpsConfig(
        organization_url=org_url,
        project=project,
        pat=pat,
        notes_field=custom_notes_field
    )

    # Then custom notes field should be used
    assert config.notes_field == "Custom.DeploymentInstructions"


def should_default_notes_field_to_custom_notes_when_not_provided():
    # Given config without notes field specified
    org_url = "https://dev.azure.com/org"
    project = "MyProject"
    pat = "token"

    # When creating config
    config = AzureDevOpsConfig(
        organization_url=org_url,
        project=project,
        pat=pat
    )

    # Then notes field should default to Custom.Notes
    assert config.notes_field == "Custom.Notes"
