import re
from collections import defaultdict
from datetime import datetime
from typing import List, Set, Dict

from models import WorkItem, Release


class MarkdownGenerator:
    WORK_ITEM_TYPE_ORDER = ['Bug', 'Epic', 'Feature', 'User Story', 'Task']

    WORK_ITEM_TYPE_EMOJIS = {
        'Bug': '🐛',
        'Epic': '📘',
        'Feature': '✨',
        'User Story': '📝',
        'Task': '🔧',
        'Issue': '⚠️',
        'Product Backlog Item': '📋',
        'Impediment': '🚧'
    }

    def __init__(self, organization_url: str, project: str) -> None:
        self.organization_url = organization_url
        self.project = project

    def generate(
        self,
        release_number: str,
        work_items: List[WorkItem],
        releases: List[Release],
        contributors: Set[str]
    ) -> str:
        lines = []
        grouped_items = self._group_work_items_by_type(work_items)

        lines.append(f"# Release Notes - {release_number}")
        lines.append("")

        self._add_summary_section(lines, work_items, releases, grouped_items)
        self._add_binaries_section(lines, releases)
        self._add_changelog_section(lines, grouped_items)
        self._add_deployment_instructions_section(lines, work_items)
        self._add_contributors_section(lines, contributors)

        return '\n'.join(lines)

    def _add_summary_section(
        self,
        lines: List[str],
        work_items: List[WorkItem],
        releases: List[Release],
        grouped_items: Dict[str, List[WorkItem]]
    ) -> None:
        lines.append("## 📊 Summary")
        lines.append("")

        release_date = self._extract_release_date(releases)
        lines.append(f"**Release Date:** {release_date}")
        lines.append("")

        iterations = self._extract_iterations(work_items)
        lines.append(f"**Iteration:** {iterations}")
        lines.append("")

        total_items = len(work_items)
        microservices_count = len(releases) if releases else 0

        lines.append(f"**Total Work Items:** {total_items}")
        lines.append(f"**Microservices Released:** {microservices_count}")
        lines.append("")

        self._add_breakdown_by_type(lines, grouped_items)

    def _extract_release_date(self, releases: List[Release]) -> str:
        if not releases:
            return 'Unreleased'

        prod_times = [r.prod_deploy_time for r in releases if r.prod_deploy_time]
        if not prod_times:
            return 'Unreleased'

        latest_time = max(prod_times)
        release_datetime = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
        return release_datetime.strftime('%B %d, %Y')

    def _extract_iterations(self, work_items: List[WorkItem]) -> str:
        if not work_items:
            return 'N/A'

        iterations = set()
        for item in work_items:
            iteration = item.iteration_path
            if iteration != 'N/A':
                iterations.add(iteration)

        if not iterations:
            return 'N/A'

        sorted_iterations = sorted(iterations, reverse=True)
        return ', '.join(sorted_iterations)

    def _add_breakdown_by_type(self, lines: List[str], grouped_items: Dict[str, List[WorkItem]]) -> None:
        lines.append("**Breakdown by Type:**")
        lines.append("")

        for work_type in self.WORK_ITEM_TYPE_ORDER:
            if work_type in grouped_items:
                count = len(grouped_items[work_type])
                emoji = self._get_work_item_type_emoji(work_type)
                lines.append(f"- {emoji} **{work_type}:** {count}")

        for work_type in sorted(grouped_items.keys()):
            if work_type not in self.WORK_ITEM_TYPE_ORDER:
                count = len(grouped_items[work_type])
                emoji = self._get_work_item_type_emoji(work_type)
                lines.append(f"- {emoji} **{work_type}:** {count}")

        lines.append("")

    def _add_binaries_section(self, lines: List[str], releases: List[Release]) -> None:
        if not releases:
            return

        lines.append("## 📦 Binaries")
        lines.append("")
        lines.append("| Microservice | Version |")
        lines.append("|--------------|---------|")

        for release in sorted(releases, key=lambda x: x.microservice):
            pipeline_url = f"{self.organization_url}/{self.project}/_release?definitionId={release.definition_id}&_a=releases&view=mine"
            release_url = f"{self.organization_url}/{self.project}/_releaseProgress?_a=release-pipeline-progress&releaseId={release.release_id}"

            microservice_link = f"[{release.microservice}]({pipeline_url})"
            version_link = f"[{release.version}]({release_url})"

            lines.append(f"| {microservice_link} | {version_link} |")

        lines.append("")

    def _add_deployment_instructions_section(self, lines: List[str], work_items: List[WorkItem]) -> None:
        items_with_notes = self._filter_items_with_notes(work_items)

        if not items_with_notes:
            return

        lines.append("## 🚀 Deployment Instructions")
        lines.append("")

        for item in items_with_notes:
            self._add_deployment_instruction_item(lines, item)

    def _filter_items_with_notes(self, work_items: List[WorkItem]) -> List[WorkItem]:
        items_with_notes = [item for item in work_items if item.notes]
        return sorted(items_with_notes, key=lambda x: x.id)

    def _add_deployment_instruction_item(self, lines: List[str], item: WorkItem) -> None:
        work_item_url = self._build_work_item_url(item.id)
        note_items = self._convert_notes_to_list_items(item.notes)

        # First line: task number as link
        lines.append(f"- [#{item.id}]({work_item_url})")

        # Sub-items: the actual instructions
        for note_item in note_items:
            lines.append(f"  - {note_item}")

        lines.append("")

    def _convert_notes_to_list_items(self, notes: str) -> List[str]:
        # Extract list items from HTML
        list_items = re.findall(r'<li>(.*?)</li>', notes, re.DOTALL)

        if list_items:
            # Clean up each list item (remove extra whitespace and HTML tags)
            cleaned_items = []
            for item in list_items:
                cleaned = re.sub(r'<[^>]+>', '', item).strip()
                if cleaned:
                    cleaned_items.append(cleaned)
            return cleaned_items
        else:
            # No list found, treat entire notes as single item
            cleaned_notes = re.sub(r'<[^>]+>', '', notes).strip()
            if cleaned_notes:
                return [cleaned_notes]
            return []

    def _build_work_item_url(self, work_item_id: int) -> str:
        return f"{self.organization_url}/{self.project}/_workitems/edit/{work_item_id}"

    def _add_changelog_section(self, lines: List[str], grouped_items: Dict[str, List[WorkItem]]) -> None:
        lines.append("## 📝 Changelog")
        lines.append("")

        for work_type in self.WORK_ITEM_TYPE_ORDER:
            if work_type in grouped_items:
                self._add_work_items_for_type(lines, work_type, grouped_items[work_type])

        for work_type in sorted(grouped_items.keys()):
            if work_type not in self.WORK_ITEM_TYPE_ORDER:
                self._add_work_items_for_type(lines, work_type, grouped_items[work_type])

    def _add_work_items_for_type(self, lines: List[str], work_type: str, items: List[WorkItem]) -> None:
        emoji = self._get_work_item_type_emoji(work_type)
        lines.append(f"### {emoji} {work_type} ({len(items)})")
        lines.append("")

        sorted_items = sorted(items, key=lambda x: x.id)

        for item in sorted_items:
            work_item_url = self._build_work_item_url(item.id)
            lines.append(f"- [#{item.id}]({work_item_url}) {item.title}")

        lines.append("")

    def _add_contributors_section(self, lines: List[str], contributors: Set[str]) -> None:
        if not contributors:
            return

        lines.append("## 👥 Contributors")
        lines.append("")
        for contributor in sorted(contributors):
            lines.append(f"- {contributor}")
        lines.append("")

    def _group_work_items_by_type(self, work_items: List[WorkItem]) -> Dict[str, List[WorkItem]]:
        grouped = defaultdict(list)
        for item in work_items:
            grouped[item.type].append(item)
        return grouped

    def _get_work_item_type_emoji(self, work_type: str) -> str:
        return self.WORK_ITEM_TYPE_EMOJIS.get(work_type, '📌')
