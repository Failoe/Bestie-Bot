import psycopg2

""" Add mogrify to all SQL statements """


def list_tags(conn, message):
	cur = conn.cursor()
	cur.execute(""" SELECT tags FROM collections""")
	results = cur.fetchall()
	return results


def delete_collection(conn, message):
	pass


def add_tag(conn, message):
	cur = conn.cursor()
	submitter = message['event']['user']
	date_added = message['event']['ts']
	item = message['event']['text'][5:].split(' ', 1)[1]
	tags = message['event']['text'][5:].split(' ', 1)[0].split('+')
	for tag in tags:
		cur.execute(cur.mogrify("""	INSERT INTO collections (submitter, item, date_added, tag) 
									VALUES (%s,%s,%s,%s) 
									ON CONFLICT (tag, item) 
									DO NOTHING""", (submitter, item, date_added, tag)))
	conn.commit()
	cur.close()

def remove_tag(conn, message):
	cur = conn.cursor()
	item = message['event']['text'][8:].split(' ', 1)[1]
	tags = message['event']['text'][8:].split(' ', 1)[0].split('+')
	print('ITEM =' + item)
	if tags == ['*']:
		cur.execute(cur.mogrify("""DELETE FROM collections WHERE item = '%s'""" % item))
	else:
		for tag in tags:
			cur.execute(cur.mogrify("""DELETE FROM collections WHERE tag = %s AND item = %s""", (tag, item)))
	conn.commit()
	cur.close()

def pick_item(conn, message):
	cur = conn.cursor()
	tag = message['event']['text'][6:].split(' ', 1)[0]
	cur.execute(cur.mogrify("""	SELECT item FROM collections
								WHERE tag = '%s'
								ORDER BY RANDOM()
								LIMIT 1""" % tag))
	conn.commit()
	response = cur.fetchone()
	cur.close()
	return response[0] if response else "Nothing found."