from pathlib import Path
from dataclasses import dataclass

@dataclass (frozen=True)
class JobData:
    source_path: Path
    destination_path: Path