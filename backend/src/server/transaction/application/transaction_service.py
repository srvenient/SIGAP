

class TransactionService:
    def __init__(self, transaction_repository):
        self.transaction_repository = transaction_repository

    def create_transaction(self, transaction_data):
        # Validate transaction data
        if not self._is_valid_transaction(transaction_data):
            raise ValueError("Invalid transaction data")

        # Create and save the transaction
        transaction = self.transaction_repository.create(transaction_data)
        return transaction

    def get_transaction(self, transaction_id):
        # Retrieve the transaction by ID
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        return transaction

    def _is_valid_transaction(self, transaction_data):
        # Implement validation logic for the transaction data
        required_fields = ["amount", "currency", "sender", "receiver"]
        for field in required_fields:
            if field not in transaction_data:
                return False
        return True