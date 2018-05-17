import pymysql
import datetime
import sys
from sqlalchemy.engine.url import make_url

# hostname = 'ou6zjjcqbi307lip.cbetxkdyhwsb.us-east-1.rds.amazonaws.com'
# username = 'wue3x6ttgfk4uior'
# password = 'ih49zj88mimvzy7d'
# database = 'apbqlpbpitcp07xo'

url = make_url("mysql://wue3x6ttgfk4uior:ih49zj88mimvzy7d@ou6zjjcqbi307lip.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/apbqlpbpitcp07xo")

def doQuery(conn):
	cur = conn.cursor()

	right_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	# query = "INSERT INTO stats(handle, freq, recent) VALUES('%s', %d, '%s')" % ("that_squeak_guy", 1, right_now)
	# query = "SELECT 'no_handle' FROM stats"
	# query = "SELECT EXISTS(SELECT 1 FROM stats WHERE handle = 'that_squeak_guy')"
	query = "SELECT freq FROM stats WHERE handle = 'test_handle'"

	# print query

	cur.execute(query)

	print cur.fetchall()[0][0];

	# for row in cur.fetchall():
	# 	print row

myConnection = pymysql.connect(host=url.host, user=url.username, passwd=url.password, db=url.database)
try:
	doQuery(myConnection)
except pymysql.err.IntegrityError as e:
	print e[0]
	# print "nope"
	sys.exit()

myConnection.commit()
myConnection.close()