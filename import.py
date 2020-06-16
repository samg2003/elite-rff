#importing necassary libraries
import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#databse connect
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#creating tables
db.execute("create table jobs (id serial primary key, title text not null, deadline text not null, description text not null)")
db.execute("create table users (id serial primary key, name text not null, password text not null)")
db.execute("create table applicant (id serial primary key,email text not null, name text not null,title text not null, description text not null, status text not null)")
db.execute("insert into users values (1, 'admin', 'admin')")
db.commit()
