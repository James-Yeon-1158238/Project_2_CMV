from dataclasses import dataclass


@dataclass
class RoleAccessResponse:

    can_edit: bool
    can_delete: bool