import pandas as pd


class StatementPersistenceService:
    def __init__(
        self,
        statement_parser,
        transaction_normalizer,
        transaction_repo
    ):
        self.statement_parser = statement_parser
        self.transaction_normalizer = transaction_normalizer
        self.transaction_repo = transaction_repo
    
    def persist(self, file_metadata: dict, file_content: bytes) -> dict:
        file_type = file_metadata["file_type"]
        column_mapping = file_metadata["column_mapping"]
        uploaded_file_id = file_metadata["uploaded_file_id"]
        
        raw_df = self.statement_parser.parse(file_content, file_type)
        normalized_df = self.transaction_normalizer.normalize(raw_df, column_mapping)
        
        transactions = []
        for _, row in normalized_df.iterrows():
            transaction = {
                "date": row["date"],
                "amount": row["amount"],
                "description": row["description"],
                "uploaded_file_id": uploaded_file_id
            }
            transactions.append(transaction)
        
        transactions_saved = self.transaction_repo.save_batch(transactions)
        
        return {
            "uploaded_file_id": uploaded_file_id,
            "transactions_saved": transactions_saved
        }
