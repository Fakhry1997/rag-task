from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ProductSpec(Base):
    """
    Normalized structured rows from client Excel files.
    Both Aurora and Horizon columns are mapped to this common schema.
    Never query without filtering by client_id.
    """

    __tablename__ = "product_specs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, nullable=False, index=True)
    source_file = Column(String, nullable=False)
    product_name = Column(String)          # product_name | product_line
    region = Column(String)                # region | market
    parameter = Column(String)             # parameter | metric
    numeric_value = Column(Float, nullable=True)   # value | metric_value
    unit = Column(String, nullable=True)   # unit | metric_unit
    limit_type = Column(String, nullable=True)      # limit_type | classification
    notes = Column(Text, nullable=True)    # notes | remarks
