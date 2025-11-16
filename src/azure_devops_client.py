import base64
import json
import logging
import urllib.error
import urllib.request
from typing import List, Set, Optional

from models import WorkItem, Release

logger = logging.getLogger(__name__)

SYSTEM_ACCOUNT_PATTERNS = [
    'Microsoft.VisualStudio.Services',
    'Project Collection Build Service',
    '<', '>'
]

MAX_DEBUG_RELEASES = 3


class AzureDevOpsClient:
    def __init__(
        self,
        organization_url: str,
        project: str,
        pat: str,
        release_field: str = 'Custom.Release',
        notes_field: str = 'Custom.Notes',
        production_environment: str = 'PROD'
    ) -> None:
        self.organization_url = organization_url
        self.project = project
        self.pat = pat
        self.release_field = release_field
        self.notes_field = notes_field
        self.production_environment = production_environment
        self.auth_header = self._create_auth_header()

    def query_work_item_ids(self, release_number: str) -> List[int]:
        wiql_query = {
            "query": f"SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], [System.IterationPath] "
                    f"FROM WorkItems WHERE [{self.release_field}] = '{release_number}' "
                    f"AND [System.TeamProject] = '{self.project}'"
        }

        url = f"{self.organization_url}/{self.project}/_apis/wit/wiql?api-version=7.0"
        data = json.dumps(wiql_query).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        })

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return [item['id'] for item in result.get('workItems', [])]
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            self._handle_api_error(e, "querying work items")

    def get_work_item_details(self, work_item_ids: List[int]) -> List[WorkItem]:
        if not work_item_ids:
            return []

        url = self._build_work_items_url(work_item_ids)
        req = urllib.request.Request(url, headers={
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        })

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return self._parse_work_items(result)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            self._handle_api_error(e, "getting work item details")

    def get_releases(self, release_tag: str) -> List[Release]:
        try:
            return self._get_classic_releases(release_tag)
        except Exception as e:
            logger.info(f"Classic Releases API not available, trying Builds API: {e}")
            return self._get_releases_from_builds(release_tag)

    def get_work_item_contributors(self, work_item_ids: List[int]) -> Set[str]:
        if not work_item_ids:
            return set()

        contributors = set()
        for work_item_id in work_item_ids:
            try:
                updates = self._fetch_work_item_updates(work_item_id)
                for update in updates:
                    contributor = self._extract_contributor(update)
                    if contributor:
                        contributors.add(contributor)
            except Exception as e:
                logger.warning(f"Could not get revisions for work item {work_item_id}: {e}")
                continue

        return contributors


    def _create_auth_header(self) -> str:
        credentials = f':{self.pat}'
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f'Basic {encoded_credentials}'

    def _handle_api_error(self, error: Exception, context: str) -> None:
        if isinstance(error, urllib.error.HTTPError):
            error_body = error.read().decode('utf-8')
            raise RuntimeError(f"Error {context}: {error.code} {error.reason}. Response: {error_body}")
        elif isinstance(error, urllib.error.URLError):
            raise RuntimeError(f"Error connecting to Azure DevOps while {context}: {error.reason}")
        else:
            raise

    def _build_work_items_url(self, work_item_ids: List[int]) -> str:
        ids_param = ','.join(map(str, work_item_ids))
        return (f"{self.organization_url}/{self.project}/_apis/wit/workitems?"
                f"ids={ids_param}&"
                f"fields=System.Id,System.Title,System.WorkItemType,System.State,System.IterationPath,{self.notes_field}&"
                f"api-version=7.0")

    def _parse_work_items(self, result: dict) -> List[WorkItem]:
        work_items = []
        for item in result.get('value', []):
            fields = item.get('fields', {})
            notes = self._parse_notes_field(fields.get(self.notes_field))
            work_items.append(WorkItem(
                id=fields.get('System.Id'),
                title=fields.get('System.Title'),
                type=fields.get('System.WorkItemType'),
                state=fields.get('System.State'),
                iteration_path=fields.get('System.IterationPath', 'N/A'),
                notes=notes
            ))
        return work_items

    def _parse_notes_field(self, raw_notes: Optional[str]) -> Optional[str]:
        if not raw_notes:
            return None

        # Only strip whitespace, preserve HTML for markdown generator to process
        cleaned_notes = raw_notes.strip()

        return cleaned_notes if cleaned_notes else None

    def _fetch_work_item_updates(self, work_item_id: int) -> List[dict]:
        url = f"{self.organization_url}/{self.project}/_apis/wit/workitems/{work_item_id}/updates?api-version=7.0"
        req = urllib.request.Request(url, headers={
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        })

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('value', [])

    def _extract_contributor(self, update: dict) -> Optional[str]:
        revised_by = update.get('revisedBy', {})
        display_name = revised_by.get('displayName')

        if display_name and not self._is_system_account(display_name):
            return display_name
        return None

    def _is_system_account(self, display_name: str) -> bool:
        return any(pattern in display_name for pattern in SYSTEM_ACCOUNT_PATTERNS)


    def _get_classic_releases(self, release_tag: str) -> List[Release]:
        vsrm_url = self._get_vsrm_url()
        url = f"{vsrm_url}/{self.project}/_apis/release/releases?api-version=7.0&$top=100&tagFilter={release_tag}&$expand=environments"

        req = urllib.request.Request(url, headers={
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        })

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            candidate_releases = result.get('value', [])
            logger.info(f"Found {len(candidate_releases)} releases matching tag filter")

            releases = []
            for release_data in candidate_releases:
                release = self._parse_classic_release(release_data)
                releases.append(release)

                if len(releases) <= MAX_DEBUG_RELEASES:
                    logger.info(f"  Found: {release.microservice} - {release.version} (PROD: {release.prod_deploy_time})")

            if releases:
                logger.info(f"Total: {len(releases)} microservice releases")
            else:
                logger.info("No releases returned from tag filter")

            return releases

    def _get_vsrm_url(self) -> str:
        if 'dev.azure.com' in self.organization_url:
            return self.organization_url.replace('dev.azure.com', 'vsrm.dev.azure.com')
        return self.organization_url

    def _parse_classic_release(self, release_data: dict) -> Release:
        pipeline_name = release_data.get('releaseDefinition', {}).get('name', 'Unknown')
        release_name = release_data.get('name', 'Unknown')
        release_id = release_data.get('id', '')
        definition_id = release_data.get('releaseDefinition', {}).get('id', '')

        prod_deploy_time = self._extract_prod_deployment_time(release_data)

        return Release(
            microservice=pipeline_name,
            version=release_name,
            prod_deploy_time=prod_deploy_time,
            release_id=release_id,
            definition_id=definition_id
        )

    def _extract_prod_deployment_time(self, release_data: dict) -> Optional[str]:
        environments = release_data.get('environments', [])
        for env in environments:
            if env.get('name') == self.production_environment:
                deploy_steps = env.get('deploySteps', [])
                if deploy_steps:
                    return deploy_steps[-1].get('lastModifiedOn')
        return None

    def _get_releases_from_builds(self, release_tag: str) -> List[Release]:
        try:
            builds_url = f"{self.organization_url}/{self.project}/_apis/build/builds?api-version=7.0&tagFilters={release_tag}&$top=100"
            req = urllib.request.Request(builds_url, headers={
                'Authorization': self.auth_header,
                'Content-Type': 'application/json'
            })

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                releases = []

                for build in result.get('value', []):
                    pipeline_name = build.get('definition', {}).get('name', 'Unknown')
                    build_number = build.get('buildNumber', 'Unknown')

                    releases.append(Release(
                        microservice=pipeline_name,
                        version=build_number
                    ))

                return releases

        except Exception as e:
            logger.warning(f"Builds API also failed: {e}. Skipping microservices section.")
            return []
