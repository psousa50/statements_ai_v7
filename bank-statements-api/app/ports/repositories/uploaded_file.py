from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID


class UploadedFileRepository(ABC):
    @abstractmethod
    def save(self, filename: str, content: bytes) -> Dict:
        pass

    @abstractmethod
    def find_by_id(self, file_id: UUID) -> Optional[Dict]:
        pass


class FileAnalysisMetadataRepository(ABC):
    @abstractmethod
    def save(
        self,
        uploaded_file_id: UUID,
        file_hash: str,
        file_type: str,
        column_mapping: Dict,
        header_row_index: int,
        data_start_row_index: int,
        normalized_sample: List[Dict],
    ) -> Dict:
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str) -> Optional[Dict]:
        pass
