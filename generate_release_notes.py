#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from collections import defaultdict
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import AzureDevOpsConfig
from azure_devops_client import AzureDevOpsClient
from markdown_generator import MarkdownGenerator
from models import WorkItem

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def get_pat_token(args: argparse.Namespace) -> str:
    pat = args.pat or os.environ.get('AZURE_DEVOPS_PAT')
    if not pat:
        raise ValueError("PAT token required. Use --pat or set AZURE_DEVOPS_PAT environment variable.")
    return pat


def group_by_type(work_items: List[WorkItem]) -> Dict[str, List[WorkItem]]:
    grouped = defaultdict(list)
    for item in work_items:
        grouped[item.type].append(item)
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate release notes from Azure DevOps work items',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_release_notes.py 2025.006 \\
    --organization https://dev.azure.com/myorg \\
    --project MyProject \\
    --pat YOUR_PAT_TOKEN

  AZURE_DEVOPS_PAT=token python generate_release_notes.py 2025.006 \\
    --organization https://dev.azure.com/myorg \\
    --project MyProject

  python generate_release_notes.py 2025.006 \\
    --organization https://dev.azure.com/myorg \\
    --project MyProject \\
    --pat YOUR_PAT_TOKEN \\
    --release-field Custom.ReleaseVersion \\
    --prod-env Production \\
    -o release_notes.md
        """
    )

    parser.add_argument(
        'release',
        help='Release number to generate notes for (e.g., 2025.006)'
    )

    parser.add_argument(
        '--organization',
        required=True,
        help='Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)'
    )

    parser.add_argument(
        '--project',
        required=True,
        help='Azure DevOps project name'
    )

    parser.add_argument(
        '--pat',
        help='Personal Access Token (can also use AZURE_DEVOPS_PAT env variable)'
    )

    parser.add_argument(
        '--release-field',
        default='Custom.Release',
        help='Work item field for release tracking (default: Custom.Release)'
    )

    parser.add_argument(
        '--prod-env',
        default='PROD',
        help='Production environment name (default: PROD)'
    )

    parser.add_argument(
        '--notes-field',
        default='System.Description',
        help='Work item field for deployment notes (default: System.Description)'
    )

    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output file path (default: Release-Notes-<release>.md)'
    )

    parser.add_argument(
        '--sort-by',
        choices=['id', 'title'],
        default='id',
        help='Sort work items by id or title (default: id)'
    )

    args = parser.parse_args()

    try:
        pat = get_pat_token(args)

        config = AzureDevOpsConfig(
            organization_url=args.organization,
            project=args.project,
            pat=pat,
            release_field=args.release_field,
            production_environment=args.prod_env,
            notes_field=args.notes_field
        )

        client = AzureDevOpsClient(
            config.organization_url,
            config.project,
            config.pat,
            config.release_field,
            config.notes_field,
            config.production_environment
        )

        logger.info(f"Querying work items for release '{args.release}'...")
        work_item_ids = client.query_work_item_ids(args.release)

        if not work_item_ids:
            logger.info(f"No work items found for release '{args.release}'")
            return

        logger.info(f"Found {len(work_item_ids)} work items")

        logger.info("Retrieving work item details...")
        work_items = client.get_work_item_details(work_item_ids)

        logger.info("Querying releases for microservices...")
        releases = client.get_releases(args.release)

        if releases:
            logger.info(f"Found {len(releases)} microservice release(s)")

        logger.info("Extracting contributors from work item history...")
        contributors = client.get_work_item_contributors(work_item_ids)

        if contributors:
            logger.info(f"Found {len(contributors)} contributor(s)")

        logger.info("Generating markdown...")
        generator = MarkdownGenerator(config.organization_url, config.project, args.sort_by)
        markdown = generator.generate(args.release, work_items, releases, contributors)

        output_file = args.output or f"Release-Notes-{args.release}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Release notes written to {output_file}")
        logger.info(f"Total work items: {len(work_items)}")

        grouped_items = group_by_type(work_items)
        for work_type, items in sorted(grouped_items.items()):
            logger.info(f"  - {work_type}: {len(items)}")

    except (ValueError, RuntimeError) as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
