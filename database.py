from os import mkdir, getcwd, access, R_OK
from os.path import join as os_join
import sqlite3

db_dir = getcwd()

connection = sqlite3.connect(os_join(db_dir, "game.db"))
connection.execute("PRAGMA foreign_keys = 1;")
cursor = connection.cursor()


def run(sql):
    cursor.execute(sql)
    connection.commit()
    return list(cursor)


def insert_score(player_name, difficulty, score):
    run(f"INSERT INTO scores (playerName, difficulty, score) VALUES ('{player_name}', '{difficulty}', {score});")


def insert_player(player_name, player_password):
    existing = run(f"SELECT playerPassword FROM accounts WHERE playerName = '{player_name}'")
    if existing:
        if existing[0][0] == player_password:
            return True
        return False

    run(f"INSERT INTO accounts (playerName, playerPassword) VALUES ('{player_name}', '{player_password}');")

    return True


def clear_accounts_table():
    run(f"DELETE FROM accounts")


def clear_scores_table():
    run(f"DELETE FROM scores")


def get_high_scores(difficulty, n):
    return run(f"SELECT playerName, score FROM scores WHERE difficulty = '{difficulty}' ORDER BY score DESC LIMIT {n}")


def get_all_scores():
    return run("SELECT * FROM scores")


def get_all_accounts():
    return run("SELECT * FROM accounts")


run("CREATE TABLE IF NOT EXISTS accounts (playerName TEXT PRIMARY KEY, playerPassword TEXT);")
run("CREATE TABLE IF NOT EXISTS scores (playerName REFERENCES accounts(playerName), difficulty TEXT, score INTEGER);")
