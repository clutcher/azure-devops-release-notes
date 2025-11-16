class AzureDevOpsConfig:
    def __init__(
        self,
        organization_url: str,
        project: str,
        pat: str,
        release_field: str = 'Custom.Release',
        production_environment: str = 'PROD',
        notes_field: str = 'Custom.Notes'
    ) -> None:
        self.organization_url = organization_url.rstrip('/')
        self.project = project
        self.pat = pat
        self.release_field = release_field
        self.production_environment = production_environment
        self.notes_field = notes_field
        self._validate_required_fields()

    def _validate_required_fields(self) -> None:
        if not self.organization_url or not self.project or not self.pat:
            raise ValueError("organization_url, project, and PAT token are required")
