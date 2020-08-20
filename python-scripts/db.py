#!/usr/bin/python
# sqlite3 db controls for plant morphology gantry operation
# 2019.06.18
# Zachary Bochanski

# Imports
################################################################################
import sqlite3


# DB setup and functions
################################################################################
# connection setup
def connection_open():
    connection = sqlite3.connect('gantrydatabase.db')
    print("connection created: ", connection)
    return connection


# create table
def create_table_ifnot_exists(sqlite_connection):
    cursor_object = sqlite_connection.cursor()
    print("cursor obj created")

    cursor_object.execute(
        "CREATE TABLE IF NOT EXISTS measurements(rowid INTEGER PRIMARY KEY, measurement_cm REAL, time_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)")

    sqlite_connection.commit()
    print("table commited")


# insert into table
def insert(connect, entities):
    cursor_object = connect.cursor()

    cursor_object.execute(
        'INSERT INTO measurements(measurement_cm) VALUES(?)', (entities,))

    connect.commit()
    print("insert commited")


# delete from table
def delete(connect):
    cursor_object = connect.cursor()

    cursor_object.execute(
        'DELETE FROM measurements WHERE rowid = (SELECT MAX(rowid) FROM measurements);')

    connect.commit()
    print("delete commited")


def connection_close(connect):
    connect.close()
    print('connection successfully closed')


if __name__ == "__main__":

    # create connnection and check if table exits
    con = connection_open()
    create_table_ifnot_exists(con)

    # insert into TABLE test
    # con = connection_setup()
    # entities = (2.3)
    # insert(con, entities)

    # delete from TABLE test
    # con = connection_setup()
    # delete(con)

    connection_close(con)
