import csv
import json
import unittest
from abc import ABC, abstractmethod


# =========================
# Custom Exceptions
# =========================

class BankingError(Exception):
    """Base exception for banking errors."""
    pass


class InvalidAccountError(BankingError):
    pass


class AccountNotFoundError(BankingError):
    pass


class InsufficientFundsError(BankingError):
    pass


class InvalidAmountError(BankingError):
    pass


class DuplicateAccountError(BankingError):
    pass


# =========================
# Bank Account Classes
# =========================

class BankAccount(ABC):
    """Base class for all bank accounts."""

    def __init__(self, account_number, holder_name, balance=0.0):

        if not account_number.strip():
            raise InvalidAccountError(
                "Account number cannot be empty."
            )

        if not holder_name.strip():
            raise InvalidAccountError(
                "Account holder name cannot be empty."
            )

        if balance < 0:
            raise InvalidAmountError(
                "Initial balance cannot be negative."
            )

        self._account_number = account_number
        self._holder_name = holder_name
        self._balance = float(balance)

    def account_number(self):
        return self._account_number

    def holder_name(self):
        return self._holder_name

    def balance(self):
        return self._balance

    def deposit(self, amount):

        if amount <= 0:
            raise InvalidAmountError(
                "Deposit amount must be greater than zero."
            )

        self._balance += amount

    def withdraw(self, amount):

        if amount <= 0:
            raise InvalidAmountError(
                "Withdrawal amount must be greater than zero."
            )

        if amount > self._balance:
            raise InsufficientFundsError(
                "Insufficient account balance."
            )

        if not self.can_withdraw(amount):
            raise InsufficientFundsError(
                "Withdrawal limit exceeded."
            )

        self._balance -= amount

    @abstractmethod
    def can_withdraw(self, amount):
        pass

    @abstractmethod
    def account_type(self):
        pass

    def to_dict(self):
        return {
            "account_number": self.account_number(),
            "holder_name": self.holder_name(),
            "balance": self.balance(),
            "account_type": self.account_type()
        }


class SavingsAccount(BankAccount):
    """Savings account with ₹1000 withdrawal limit."""

    WITHDRAWAL_LIMIT = 1000

    def can_withdraw(self, amount):
        return amount <= self.WITHDRAWAL_LIMIT

    def account_type(self):
        return "Savings"


class CurrentAccount(BankAccount):
    """Current account with ₹10000 withdrawal limit."""

    WITHDRAWAL_LIMIT = 10000

    def can_withdraw(self, amount):
        return amount <= self.WITHDRAWAL_LIMIT

    def account_type(self):
        return "Current"


# =========================
# Banking Ledger
# =========================

class BankingLedger:
    """Manages accounts and transactions."""

    def __init__(self):
        self._accounts = {}
        self._transactions = []

    def accounts(self):
        return self._accounts.copy()

    def transactions(self):
        return self._transactions.copy()

    def add_account(self, account):

        if account.account_number() in self._accounts:
            raise DuplicateAccountError(
                "Account already exists."
            )

        self._accounts[account.account_number()] = account

    def get_account(self, account_number):

        if account_number not in self._accounts:
            raise AccountNotFoundError(
                "Account not found."
            )

        return self._accounts[account_number]

    def deposit(self, account_number, amount):

        account = self.get_account(account_number)

        account.deposit(amount)

        self._record_transaction(
            "DEPOSIT",
            account_number,
            None,
            amount
        )

    def withdraw(self, account_number, amount):

        account = self.get_account(account_number)

        account.withdraw(amount)

        self._record_transaction(
            "WITHDRAW",
            account_number,
            None,
            amount
        )

    def transfer(self, from_account, to_account, amount):

        if amount <= 0:
            raise InvalidAmountError(
                "Transfer amount must be greater than zero."
            )

        sender = self.get_account(from_account)
        receiver = self.get_account(to_account)

        sender.withdraw(amount)
        receiver.deposit(amount)

        self._record_transaction(
            "TRANSFER",
            from_account,
            to_account,
            amount
        )

    def _record_transaction(
        self,
        transaction_type,
        from_account,
        to_account,
        amount
    ):
        self._transactions.append({
            "type": transaction_type,
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount
        })


# =========================
# Storage Manager
# =========================

class StorageManager:

    @staticmethod
    def save_json(ledger, filename):

        data = []

        for account in ledger.accounts().values():
            data.append(account.to_dict())

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    @staticmethod
    def load_json(filename):

        ledger = BankingLedger()

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        for account_data in data:

            if account_data["account_type"] == "Savings":

                account = SavingsAccount(
                    account_data["account_number"],
                    account_data["holder_name"],
                    account_data["balance"]
                )

            elif account_data["account_type"] == "Current":

                account = CurrentAccount(
                    account_data["account_number"],
                    account_data["holder_name"],
                    account_data["balance"]
                )

            else:
                raise InvalidAccountError(
                    "Unknown account type."
                )

            ledger.add_account(account)

        return ledger

    @staticmethod
    def save_csv(ledger, filename):

        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            fieldnames = [
                "type",
                "from_account",
                "to_account",
                "amount"
            ]

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            for transaction in ledger.transactions():
                writer.writerow(transaction)


# =========================
# Unit Tests
# =========================

class TestBankingLedger(unittest.TestCase):

    def setUp(self):

        self.ledger = BankingLedger()

        self.savings = SavingsAccount(
            "S001",
            "Rahul",
            5000
        )

        self.current = CurrentAccount(
            "C001",
            "Priya",
            10000
        )

        self.ledger.add_account(self.savings)
        self.ledger.add_account(self.current)

    def test_account_creation(self):

        self.assertEqual(
            self.savings.account_number(),
            "S001"
        )

        self.assertEqual(
            self.savings.balance(),
            5000
        )

    def test_deposit(self):

        self.ledger.deposit(
            "S001",
            1000
        )

        self.assertEqual(
            self.savings.balance(),
            6000
        )

    def test_withdraw(self):

        self.ledger.withdraw(
            "S001",
            500
        )

        self.assertEqual(
            self.savings.balance(),
            4500
        )

    def test_transfer(self):

        self.ledger.transfer(
            "S001",
            "C001",
            1000
        )

        self.assertEqual(
            self.savings.balance(),
            4000
        )

        self.assertEqual(
            self.current.balance(),
            11000
        )

    def test_invalid_deposit(self):

        with self.assertRaises(InvalidAmountError):
            self.ledger.deposit(
                "S001",
                -100
            )

    def test_insufficient_funds(self):

        with self.assertRaises(InsufficientFundsError):
            self.ledger.withdraw(
                "S001",
                10000
            )

    def test_account_not_found(self):

        with self.assertRaises(AccountNotFoundError):
            self.ledger.get_account("X999")

    def test_duplicate_account(self):

        with self.assertRaises(DuplicateAccountError):
            self.ledger.add_account(
                SavingsAccount(
                    "S001",
                    "Another User"
                )
            )

    def test_invalid_account(self):

        with self.assertRaises(InvalidAccountError):
            SavingsAccount(
                "",
                "Test User"
            )

    def test_withdrawal_limit(self):

        with self.assertRaises(InsufficientFundsError):
            self.ledger.withdraw(
                "S001",
                2000
            )

    def test_transaction_record(self):

        self.ledger.deposit(
            "S001",
            500
        )

        self.assertEqual(
            len(self.ledger.transactions()),
            1
        )

        self.assertEqual(
            self.ledger.transactions()[0]["type"],
            "DEPOSIT"
        )


# =========================
# Main Program
# =========================

def main():

    print("=" * 55)
    print("       BANKING LEDGER MANAGEMENT SYSTEM")
    print("=" * 55)

    ledger = BankingLedger()

    try:

        savings = SavingsAccount(
            "S001",
            "Rahul",
            5000
        )

        current = CurrentAccount(
            "C001",
            "Priya",
            10000
        )

        ledger.add_account(savings)
        ledger.add_account(current)

        print("\nAccounts created successfully.")

        ledger.deposit(
            "S001",
            1000
        )

        print("₹1000 deposited into S001.")

        ledger.withdraw(
            "C001",
            2000
        )

        print("₹2000 withdrawn from C001.")

        ledger.transfer(
            "S001",
            "C001",
            500
        )

        print("₹500 transferred from S001 to C001.")

        # Display accounts
        print("\nACCOUNT DETAILS")
        print("-" * 55)

        for account in ledger.accounts().values():

            print(
                f"Account Number : {account.account_number()}"
            )

            print(
                f"Holder Name    : {account.holder_name()}"
            )

            print(
                f"Account Type   : {account.account_type()}"
            )

            print(
                f"Balance        : ₹{account.balance()}"
            )

            print("-" * 55)

        StorageManager.save_json(
            ledger,
            "accounts.json"
        )

        StorageManager.save_csv(
            ledger,
            "transactions.csv"
        )

        print("\nData successfully saved.")
        print("Created: accounts.json")
        print("Created: transactions.csv")

    except BankingError as error:

        print(
            f"\nBanking Error: {error}"
        )


if __name__ == "__main__":

    main()

    print("\nRunning Unit Tests...")
    print("=" * 55)

    unittest.main(
        argv=["first-arg-is-ignored"],
        exit=False
    )