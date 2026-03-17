def validate_client_access(resource_client_id: str, requesting_client_id: str) -> None:
    """
    Raise PermissionError if the requesting client does not own the resource.
    Call this before every cross-client data access.
    """
    if resource_client_id != requesting_client_id:
        raise PermissionError(
            f"Client '{requesting_client_id}' is not authorised to access "
            f"resources belonging to '{resource_client_id}'."
        )
