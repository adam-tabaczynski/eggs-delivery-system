from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.interfaces.customer_repository import CustomerRepository
from src.models import Customer


class SqlAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, customer_id: int) -> Customer | None:
        return self.session.get(Customer, customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return self.session.scalar(select(Customer).where(Customer.email == email))

    def add(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.flush()
        self.session.refresh(customer)
        return customer
