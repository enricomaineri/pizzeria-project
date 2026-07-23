from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine
from app import db_models


sqlite_file_name = "vesuvio.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


# pysqlite gestisce le transazioni in modo inaffidabile per la concorrenza:
# un BEGIN (deferred) di default non prende subito il lock di scrittura, quindi
# richieste concorrenti possono leggere lo stesso stato "prima" del controllo
# capacità slot e prenotare entrambe lo stesso posto (race condition verificata
# con test di concorrenza reale: overbooking oltre il limite configurato).
# Disabilitiamo la gestione automatica di pysqlite ed emettiamo noi un
# BEGIN IMMEDIATE esplicito a ogni transazione, cosi' il lock di scrittura
# viene preso subito e le transazioni concorrenti si serializzano davvero.
@event.listens_for(engine, "connect")
def _sqlite_disable_pysqlite_begin(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None


@event.listens_for(engine, "begin")
def _sqlite_begin_immediate(conn):
    conn.exec_driver_sql("BEGIN IMMEDIATE")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session