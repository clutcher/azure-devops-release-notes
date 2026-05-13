import pytest
from markdown_generator import MarkdownGenerator
from models import WorkItem, Release, E2ETestResults


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

    # Then should show counts collapsed into a single line
    assert "**Work Items:** 4 across 2 microservices" in markdown


def should_omit_microservice_clause_when_no_releases_available(generator, sample_work_items):
    # Given work items but no releases (e.g., Builds-API fallback)
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, [], set())

    # Then should show only the work item count
    assert "**Work Items:** 4" in markdown
    assert "across" not in markdown


def should_group_audit_lines_with_soft_line_break(generator, sample_work_items, sample_releases):
    # Given releases with approver and deployer
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, set())

    # Then audit lines preceding others should end with two trailing spaces (Markdown <br>)
    assert "**Release Date:** November 06, 2025  \n" in markdown
    assert "**Approved By:** Alice Approver  \n" in markdown
    # And the iteration line (scope group, has count after it) should also end with two spaces
    iteration_line = next(line for line in markdown.split("\n") if line.startswith("**Iteration:"))
    assert iteration_line.endswith("  ")


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


def should_sort_work_items_by_id_when_sort_by_id(generator):
    # Given work items in random order
    work_items = [
        WorkItem(id=5, title="Alpha", type="Bug", state="Done"),
        WorkItem(id=1, title="Charlie", type="Bug", state="Done"),
        WorkItem(id=3, title="Beta", type="Bug", state="Done"),
    ]

    # When sorting
    sorted_items = generator._sort_work_items(work_items)

    # Then should be sorted by ID
    assert [item.id for item in sorted_items] == [1, 3, 5]


def should_sort_work_items_by_title_when_sort_by_title(organization_url, project_name):
    # Given generator with title sorting
    generator = MarkdownGenerator(organization_url, project_name, sort_by='title')
    work_items = [
        WorkItem(id=5, title="Charlie", type="Bug", state="Done"),
        WorkItem(id=1, title="Alpha", type="Bug", state="Done"),
        WorkItem(id=3, title="Beta", type="Bug", state="Done"),
    ]

    # When sorting
    sorted_items = generator._sort_work_items(work_items)

    # Then should be sorted by title alphabetically
    assert [item.title for item in sorted_items] == ["Alpha", "Beta", "Charlie"]


def should_group_work_items_by_parent_when_requested(organization_url, project_name):
    # Given work items with different parents
    work_items = [
        WorkItem(id=1, title="Task 1", type="Bug", state="Done", parent_id=100),
        WorkItem(id=2, title="Task 2", type="Bug", state="Done", parent_id=100),
        WorkItem(id=3, title="Task 3", type="Bug", state="Done", parent_id=200),
        WorkItem(id=4, title="Task 4", type="Bug", state="Done", parent_id=None),
    ]
    generator = MarkdownGenerator(organization_url, project_name)

    # When grouping by parent
    grouped = generator._group_work_items_by_parent(work_items)

    # Then should group correctly
    assert len(grouped[100]) == 2
    assert len(grouped[200]) == 1
    assert len(grouped[None]) == 1


def should_show_parent_headers_when_group_by_parent_enabled(organization_url, project_name):
    # Given generator with group_by_parent enabled
    generator = MarkdownGenerator(organization_url, project_name, group_by_parent=True)
    work_items = [
        WorkItem(id=1, title="Fix bug", type="Bug", state="Done", parent_id=100, parent_title="Epic: Authentication"),
        WorkItem(id=2, title="Another bug", type="Bug", state="Done", parent_id=100, parent_title="Epic: Authentication"),
    ]

    # When generating markdown
    markdown = generator.generate("2025.006", work_items, [], set())

    # Then should include parent header
    assert "#### [#100]" in markdown
    assert "Epic: Authentication" in markdown


def should_show_standalone_items_section_when_orphans_exist(organization_url, project_name):
    # Given generator with group_by_parent enabled and orphan items
    generator = MarkdownGenerator(organization_url, project_name, group_by_parent=True)
    work_items = [
        WorkItem(id=1, title="Fix bug", type="Bug", state="Done", parent_id=None),
        WorkItem(id=2, title="Another bug", type="Bug", state="Done", parent_id=None),
    ]

    # When generating markdown
    markdown = generator.generate("2025.006", work_items, [], set())

    # Then should include Standalone Items section
    assert "#### 📌 Standalone Items" in markdown


def should_show_approver_in_summary_when_releases_have_approver(generator, sample_work_items, sample_releases):
    # Given releases approved by the same person
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, set())

    # Then summary should include single approver name
    assert "**Approved By:** Alice Approver" in markdown


def should_show_deployer_in_summary_when_releases_have_deployer(generator, sample_work_items, sample_releases):
    # Given releases deployed by the same person
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, sample_releases, set())

    # Then summary should include single deployer name
    assert "**Deployed By:** Bob Deployer" in markdown


def should_join_unique_approvers_when_releases_have_different_approvers(generator, sample_work_items):
    # Given releases with different approvers
    releases = [
        Release(microservice="svc-a", version="v1", prod_approved_by="Alice Approver", prod_deployed_by="Bob Deployer"),
        Release(microservice="svc-b", version="v2", prod_approved_by="Charlie Approver", prod_deployed_by="Bob Deployer"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, releases, set())

    # Then approvers should be comma-joined in sorted order
    assert "**Approved By:** Alice Approver, Charlie Approver" in markdown


def should_omit_approver_line_when_no_release_has_approver(generator, sample_work_items):
    # Given releases without approver info
    releases = [
        Release(microservice="svc-a", version="v1"),
        Release(microservice="svc-b", version="v2"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, releases, set())

    # Then approver line should be absent
    assert "**Approved By:**" not in markdown


def should_omit_deployer_line_when_no_release_has_deployer(generator, sample_work_items):
    # Given releases without deployer info
    releases = [
        Release(microservice="svc-a", version="v1"),
        Release(microservice="svc-b", version="v2"),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, releases, set())

    # Then deployer line should be absent
    assert "**Deployed By:**" not in markdown


def should_ignore_empty_approver_when_extracting(generator, sample_work_items):
    # Given one release with approver and one with empty string
    releases = [
        Release(microservice="svc-a", version="v1", prod_approved_by="Alice Approver"),
        Release(microservice="svc-b", version="v2", prod_approved_by=""),
    ]
    release_number = "2025.006"

    # When generating markdown
    markdown = generator.generate(release_number, sample_work_items, releases, set())

    # Then only the non-empty approver should appear
    assert "**Approved By:** Alice Approver" in markdown


def should_not_show_parent_headers_when_group_by_parent_disabled(organization_url, project_name):
    # Given generator with group_by_parent disabled (default)
    generator = MarkdownGenerator(organization_url, project_name, group_by_parent=False)
    work_items = [
        WorkItem(id=1, title="Fix bug", type="Bug", state="Done", parent_id=100, parent_title="Epic: Authentication"),
    ]

    # When generating markdown
    markdown = generator.generate("2025.006", work_items, [], set())

    # Then should NOT include parent header (just flat list)
    assert "#### [#100]" not in markdown
    assert "Standalone Items" not in markdown


def should_generate_e2e_section_with_all_fields(organization_url, project_name):
    # Given generator and E2E test results
    generator = MarkdownGenerator(organization_url, project_name)
    results = E2ETestResults(
        build_id="12345",
        passed=42,
        failed=3,
        skipped=5,
        total=50,
        pass_rate=84.0,
        build_url="https://dev.azure.com/org/project/_build/results?buildId=12345",
        test_run_url="https://dev.azure.com/org/project/_testManagement/runs?runId=999"
    )

    # When generating E2E section
    markdown = generator.generate_e2e_section(results)

    # Then should include all E2E information
    assert "## 🧪 E2E Test Results" in markdown
    assert "[#12345]" in markdown
    assert "View Test Results" in markdown
    assert "| ✅ Passed | 42 |" in markdown
    assert "| ❌ Failed | 3 |" in markdown
    assert "| ⏭️ Skipped | 5 |" in markdown
    assert "**Total:** 50" in markdown
    assert "**Pass Rate:** 84.0%" in markdown


def should_generate_e2e_section_without_test_run_url(organization_url, project_name):
    # Given generator and E2E test results without test_run_url
    generator = MarkdownGenerator(organization_url, project_name)
    results = E2ETestResults(
        build_id="12345",
        passed=10,
        failed=0,
        skipped=0,
        total=10,
        pass_rate=100.0,
        build_url="https://dev.azure.com/org/project/_build/results?buildId=12345",
        test_run_url=None
    )

    # When generating E2E section
    markdown = generator.generate_e2e_section(results)

    # Then should include build link but not test run link
    assert "[#12345]" in markdown
    assert "View Test Results" not in markdown
    assert "**Pass Rate:** 100.0%" in markdown


def should_generate_e2e_section_with_correct_table_format(organization_url, project_name):
    # Given generator and E2E test results
    generator = MarkdownGenerator(organization_url, project_name)
    results = E2ETestResults(
        build_id="999",
        passed=0,
        failed=10,
        skipped=0,
        total=10,
        pass_rate=0.0,
        build_url="https://example.com",
        test_run_url=None
    )

    # When generating E2E section
    markdown = generator.generate_e2e_section(results)

    # Then should have correct markdown table structure
    assert "| Status | Count |" in markdown
    assert "|--------|-------|" in markdown
    assert "| ❌ Failed | 10 |" in markdown
    assert "**Pass Rate:** 0.0%" in markdown
