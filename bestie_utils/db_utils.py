import psycopg2
import configparser


def pgsql_connect(config_path):
	config = configparser.ConfigParser()
	config.read(config_path)
	conn = psycopg2.connect(
		database=config['PostgreSQL']['database'],
		user=config['PostgreSQL']['user'],
		password=config['PostgreSQL']['password'],
		host=config['PostgreSQL']['host'],
		port=config['PostgreSQL']['port'])
	return conn


def drop(conn, tablename):
	try:
		cur = conn.cursor()
		cur.execute("DROP TABLE " + tablename)
		conn.commit()
	except:
		conn.commit()


def build_bestcoinDB(conn):
	init_cur = conn.cursor()

	drop(conn, "bestcoin_log")
	init_cur.execute("""CREATE TABLE bestcoin_log (
		payer_id text,
		recipient_id text,
		note text,
		transaction_time timestamp,
		transaction_id int
		);""")

	drop(conn, "bestcoin_wallets")
	init_cur.execute("""CREATE TABLE bestcoin_wallets (
		coins real,
		user_id text
		);""")

	conn.commit()
	init_cur.close()


def build_collectionsDB(conn):
	init_cur = conn.cursor()

	drop(conn, "collections")
	init_cur.execute("""CREATE TABLE collections (
		submitter text,
		item text,
		date_added real,
		tag text,
		UNIQUE (tag, item)
		);""")

	conn.commit()
	init_cur.close()


def build_userDB(conn):
	init_cur = conn.cursor()

	drop(conn, "user_info")
	init_cur.execute("""CREATE TABLE user_info (
		user_id text,
		user_name text,
		role text
		);""")

	conn.commit()
	init_cur.close()

def main():
	conn = pgsql_connect('../bestie.config')
	build_bestcoinDB(conn)
	build_collectionsDB(conn)
	build_userDB(conn)

if __name__ == '__main__':
	main()