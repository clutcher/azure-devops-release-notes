from dataclasses import dataclass
from typing import Optional


@dataclass
class WorkItem:
    id: int
    title: str
    type: str
    state: str
    iteration_path: str = 'N/A'
    notes: Optional[str] = None


@dataclass
class Release:
    microservice: str
    version: str
    prod_deploy_time: Optional[str] = None
    release_id: str = ''
    definition_id: str = ''
