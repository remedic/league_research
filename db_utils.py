#!/usr/bin/env python

#Python code to initialize MYSQL database to store tennis record data

import mysql.connector as mysql

def main():

    db = mysql.connect(host="localhost", user="root", passwd="password")

    mydb = db.cursor()
    
    create_db(mydb)

    mydb.execute('USE tennis_record')

    create_db_tables(mydb)

    mydb.close()

def create_db(mydb):

    sql = 'CREATE DATABASE IF NOT EXISTS tennis_record'
    mydb.execute(sql)

def create_db_tables(mydb):

    #Create match table
    sql = '''CREATE TABLE IF NOT EXISTS MATCHES(
        MATCH_ID VARCHAR(256) PRIMARY KEY,
        MATCH_DATE DATE,
        LEAGUE VARCHAR(100),
        TEAM_1 VARCHAR(100),
        TEAM_2 VARCHAR(100),
        COURT VARCHAR(100),
        WIN_TEAM VARCHAR(100),
        TEAM1_GAMES INT(6),
        TEAM2_GAMES INT(6),
        DELTA_PCT_GAMES FLOAT(6),
        TEAM1_P1_IR FLOAT(6),
        TEAM1_P2_IR FLOAT(6),
        TEAM2_P1_IR FLOAT(6),
        TEAM2_P2_IR FLOAT(6),
        TEAM1_AVG_IR FLOAT(6),
        TEAM2_AVG_IR FLOAT(6),
        DELTA_TEAM_IR FLOAT(6),
        TEAM1_P1_MR FLOAT(6),
        TEAM1_P2_MR FLOAT(6),
        TEAM2_P1_MR FLOAT(6),
        TEAM2_P2_MR FLOAT(6),
        TEAM1_AVG_MR FLOAT(6),
        TEAM2_AVG_MR FLOAT(6),
        DELTA_TEAM_MR FLOAT(6)
    )
    '''
    mydb.execute(sql)



#CREATE


#READ
#UPDATE
#DELETE

if __name__=="__main__":
    main()
