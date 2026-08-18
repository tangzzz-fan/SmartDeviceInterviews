from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImportReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "added": self.added,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "skipped_files": self.skipped_files,
            "errors": self.errors,
            "summary": {
                "added": len(self.added),
                "updated": len(self.updated),
                "unchanged": len(self.unchanged),
                "skipped_files": len(self.skipped_files),
                "errors": len(self.errors),
            },
        }
