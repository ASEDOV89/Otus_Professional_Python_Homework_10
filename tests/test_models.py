import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Sale
from datetime import date


@pytest.fixture(scope="module")
def test_db():
    # In-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_sale_model(test_db):
    new_sale = Sale(sale_date=date(2025, 1, 1), quantity=5, item_id=1)
    test_db.add(new_sale)
    test_db.commit()

    fetched_sale = test_db.query(Sale).filter_by(item_id=1).first()
    assert fetched_sale is not None
    assert fetched_sale.quantity == 5
