import pytest
from markdown_generator import MarkdownGenerator
from models import WorkItem, Release


@pytest.fixture
def generator(organization_url, project_name):
    return MarkdownGenerator(organization_url, project_name)


def should_initialize_generator_with_org_and_project_when_created(generator, organization_url, project_name):
    # Given generator is initialized with organization and project
    # When checking generator properties
    # Then should have correct values
    assert generator.organization_url == organization_url
    assert generator.project == project_name


def should_return_emoji_for_known_type_when_requested(generator):
    # Given known work item types
    # When getting emojis for each type
    # Then should return correct emoji
    assert generator._get_work_item_type_emoji('Bug') == '🐛'
    assert generator._get_work_item_type_emoji('Feature') == '✨'
    assert generator._get_work_item_type_emoji('Task') == '🔧'
    assert generator._get_work_item_type_emoji('Unknown Type') == '📌'


def should_group_work_items_by_type_when_provided(generator, sample_work_items):
    # Given a list of work items with different types
    # When grouping by type
    grouped = generator._group_work_items_by_type(sample_work_items)

    # Then should have all types grouped correctly
    assert 'Bug' in grouped
    assert 'Feature' in grouped
    assert 'Task' in grouped
    assert 'User Story' in grouped
    assert len(grouped['Bug']) == 1
    assert len(grouped['Feature']) == 1
    assert len(grouped['Task']) == 1
    assert len(grouped['User Story']) == 1


def should_extract_and_sort_iterations_when_work_items_provided(generator, sample_work_items):
    # Given work items with multiple iterations
    # When extracting iterations
    iterations = generator._extract_iterations(sample_work_items)

    # Then should return sorted iterations (newest first)
    assert 'Sprint 2' in iterations
    assert 'Sprint 1' in iterations
    assert iterations.startswith('Sprint 2')


def should_return_na_when_no_work_items_for_iterations(generator):
    # Given empty work items list
    # When extracting iterations
    iterations = generator._extract_iterations([])

    # Then should return N/A
    assert iterations == 'N/A'


def should_return_na_when_all_iterations_are_na(generator):
    # Given work items with only N/A iterations
    items = [
        WorkItem(id=1, title="Test", type="Bug", state="Done", iteration_path="N/A"),
        WorkItem(id=2, title="Test2", type="Bug", state="Done", iteration_path="N/A"),
    ]

    # When extracting iterations
    iterations = generator._extract_iterations(items)

    # Then should return N/A
    assert iterations == 'N/A'


def should_extract_latest_release_date_when_releases_provided(generator, sample_releases):
    # Given releases with production deployment times
    # When extracting release date
    date = generator._extract_release_date(sample_releases)

    # Then should return latest deployment date formatted
    assert date == 'November 06, 2025'


def should_return_unreleased_when_no_releases(generator):
    # Given empty releases list
    # When extracting release date
    date = generator._extract_release_date([])

    # Then should return Unreleased
    assert date == 'Unreleased'


def should_generate_all_sections_when_all_data_provided(generator, sample_work_items, sample_releases, sample_contributors):
    # Given release data with all sections populated
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, sample_contributors)

    # Then should include all sections
    assert "# Release Notes - 2025.006" in markdown
    assert "## 📊 Summary" in markdown
    assert "## 📦 Binaries" in markdown
    assert "## 📝 Changelog" in markdown
    assert "## 👥 Contributors" in markdown


def should_include_work_item_titles_when_generating(generator, sample_work_items):
    # Given work items with specific titles
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then should include all work item titles
    assert "Fix login bug" in markdown
    assert "Add user dashboard" in markdown
    assert "Update API docs" in markdown


def should_include_release_details_when_generating(generator, sample_work_items, sample_releases):
    # Given releases with microservices and versions
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, set())

    # Then should include release information
    assert "auth-service" in markdown
    assert "api-gateway" in markdown
    assert "v1.2.3" in markdown
    assert "v2.0.1" in markdown


def should_include_contributor_names_when_generating(generator, sample_work_items, sample_contributors):
    # Given a set of contributors
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], sample_contributors)

    # Then should include all contributor names
    assert "Alice Developer" in markdown
    assert "Bob Engineer" in markdown
    assert "Charlie Tester" in markdown


def should_hide_binaries_section_when_no_releases(generator, sample_work_items):
    # Given no releases
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then binaries section should not appear
    assert "## 📦 Binaries" not in markdown


def should_hide_contributors_section_when_no_contributors(generator, sample_work_items):
    # Given no contributors
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then contributors section should not appear
    assert "## 👥 Contributors" not in markdown


def should_sort_work_items_by_id_when_generating(generator):
    # Given work items in random order
    work_items = [
        WorkItem(id=5, title="Item 5", type="Bug", state="Done"),
        WorkItem(id=1, title="Item 1", type="Bug", state="Done"),
        WorkItem(id=3, title="Item 3", type="Bug", state="Done"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then items should be sorted by ID in output
    item1_pos = markdown.find("Item 1")
    item3_pos = markdown.find("Item 3")
    item5_pos = markdown.find("Item 5")
    assert item1_pos < item3_pos < item5_pos


def should_display_summary_statistics_when_generating(generator, sample_work_items, sample_releases):
    # Given work items and releases
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, set())

    # Then should show correct statistics
    assert "**Total Work Items:** 4" in markdown
    assert "**Microservices Released:** 2" in markdown


def should_display_breakdown_by_type_when_generating(generator, sample_work_items):
    # Given work items of different types
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then should show breakdown with counts
    assert "**Breakdown by Type:**" in markdown
    assert "**Bug:** 1" in markdown
    assert "**Feature:** 1" in markdown
    assert "**Task:** 1" in markdown
    assert "**User Story:** 1" in markdown


def should_hide_deployment_instructions_when_no_work_items_have_notes(generator, sample_work_items):
    # Given work items without notes
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then deployment instructions section should not appear
    assert "## 🚀 Deployment Instructions" not in markdown


def should_show_deployment_instructions_when_work_items_have_notes(generator):
    # Given work items with notes
    work_items = [
        WorkItem(id=1, title="Fix login bug", type="Bug", state="Done", notes="Deploy to production first"),
        WorkItem(id=2, title="Add user dashboard", type="Feature", state="Done", notes="Restart app services after deployment"),
        WorkItem(id=3, title="Update API docs", type="Task", state="Done", notes=None),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then deployment instructions section should appear with notes
    assert "## 🚀 Deployment Instructions" in markdown
    assert "Deploy to production first" in markdown
    assert "Restart app services after deployment" in markdown


def should_sort_deployment_instructions_by_id_when_generating(generator):
    # Given work items with notes in random order
    work_items = [
        WorkItem(id=5, title="Item 5", type="Bug", state="Done", notes="Step 5"),
        WorkItem(id=1, title="Item 1", type="Bug", state="Done", notes="Step 1"),
        WorkItem(id=3, title="Item 3", type="Bug", state="Done", notes="Step 3"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then items should be sorted by ID in deployment instructions
    step1_pos = markdown.find("Step 1")
    step3_pos = markdown.find("Step 3")
    step5_pos = markdown.find("Step 5")
    assert step1_pos < step3_pos < step5_pos


def should_include_work_item_links_in_deployment_instructions_when_generating(generator, organization_url, project_name):
    # Given work items with notes
    work_items = [
        WorkItem(id=123, title="Deploy feature", type="Feature", state="Done", notes="Deploy instructions here"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then should include work item links and instructions
    expected_url = f"{organization_url}/{project_name}/_workitems/edit/123"
    assert "[#123]" in markdown
    assert expected_url in markdown
    assert "Deploy instructions here" in markdown


def should_convert_html_list_to_markdown_list_when_generating_deployment_instructions(generator, organization_url, project_name):
    # Given work items with HTML list in notes
    work_items = [
        WorkItem(id=1, title="Setup feature", type="Feature", state="Done",
                 notes="<ul><li>Step one</li><li>Step two</li><li>Step three</li></ul>"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then should show task number first with notes as sub-items
    expected_url = f"{organization_url}/{project_name}/_workitems/edit/1"
    assert f"- [#1]({expected_url})" in markdown
    assert "  - Step one" in markdown
    assert "  - Step two" in markdown
    assert "  - Step three" in markdown


def should_show_task_number_first_with_single_instruction_as_subitem_when_generating(generator, organization_url, project_name):
    # Given work items with single instruction
    work_items = [
        WorkItem(id=456, title="Configure deployment", type="Feature", state="Done",
                 notes="Update configuration"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, work_items, [], set())

    # Then should show task number first with instruction as sub-item
    expected_url = f"{organization_url}/{project_name}/_workitems/edit/456"
    assert f"- [#456]({expected_url})" in markdown
    assert "  - Update configuration" in markdown
