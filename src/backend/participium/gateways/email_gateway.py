from __future__ import annotations


class EmailGateway:
    def send(self, email: str, title: str, body: str) -> None:
        print("Simulating email send operation.")
