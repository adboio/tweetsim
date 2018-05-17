import web
from web import form
import random
from scrape import get_all_tweets
import tweepy
from markovbot import MarkovBot
import pymysql
from sqlalchemy.engine.url import make_url
import datetime
import os

web.config.debug = False

urls = (
	'/', 'home',
	'/tweet', 'generator'
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'tweets': [], 's_handle': ""})
render = web.template.render('templates/')


handle_form = form.Form(
	form.Textbox("handle",
		form.notnull,
		form.regexp('^\w{1,15}$', 'Must be 15 characters or less, no spaces'),
		# form.Validator('Must be 15 characters or less', lambda x:len(x) <= 15),
		description="@")
)

class home:

	# GET declares this session's tweets (if not done yet)
	#     and renders the home page where a user can enter a @handle
	def GET(self):
		if 'tweets' not in session:
			session.tweets = []
		else:
			session.tweets = []
		form = handle_form()
		return render.home(form)

	# POST validates the handle and, if valid, sets it to this
	#      session's s_handle variable
	def POST(self):
		form = handle_form()

		if not form.validates():
			return render.home(form)
		else:
			handle = form.d.handle

			if 's_handle' not in session:
				s_handle = ""

			session.s_handle = handle

			## CONNECT TO DATABASE
			DATABASE_URL = os.environ.get('JAWSDB_URL')
			db_url = make_url(DATABASE_URL)

			conn = pymysql.connect(
							host=db_url.host,
							user=db_url.username,
							passwd=db_url.password,
							db=db_url.database
						)

			cur = conn.cursor()

			## LOOKUP ENTRY
			found = int(self.db_lookup(cur, session.s_handle))

			## GET CURRENT TIME
			rn = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

			## UPDATE EXISTING OR INSERT NEW
			if found == 1:
				# self.inc_freq(cur, conn, handle)
				freq = int(self.get_freq(cur, handle)) + 1
				query = "UPDATE stats SET freq = %d, recent = '%s' WHERE handle = '%s'" % (freq, rn, handle)
				cur.execute(query)
				conn.commit()
			else:
				query = "INSERT INTO stats(handle, freq, recent) VALUES('%s', 1, '%s')" % (handle, rn)
				try:
					cur.execute(query)
					conn.commit()
				except:
					# do something about that here
					print "oh no"

			## DISCONNECT FROM DATABASE
			conn.close()

			## MOVE TO GENERATED PAGE
			raise web.seeother('/tweet')

	def db_lookup(self, cur, handle):
		query = "SELECT EXISTS(SELECT 1 FROM stats WHERE handle = '%s')" % handle
		cur.execute(query)

		return cur.fetchall()[0][0]

	def get_freq(self, cur, handle):
		query = "SELECT freq FROM stats WHERE handle = '%s'" % handle
		cur.execute(query)

		return cur.fetchall()[0][0]

	# def inc_freq(self, cur, conn, handle):
	# 	rn = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	# 	freq = int(self.get_freq(cur, handle)) + 1
	# 	query = "UPDATE stats SET freq = %d, recent = '%s' WHERE handle = '%s'" % (freq, rn, handle)
	# 	cur.execute(query)
	# 	conn.commit()

	# def db_insert(self, cur, conn, handle):
	# 	rn = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	# 	query = "INSERT INTO stats(handle, freq, recent) VALUES('%s', 1, '%s')" % (handle, rn)

	# 	try:
	# 		cur.execute(query)
	# 		conn.commit()
	# 	except:
	# 		# do something about that here
	# 		print "oh no"

class generator:

	# GET checks for the session's handle and generates tweet if found
	def GET(self):
		if 's_handle' not in session:
			raise web.seeother('/')
		else:
			return self.tweet_gen(session.s_handle)

	# POST only used to "generate another" tweet; calls on itself
	def POST(self):
		return self.GET()

	# tweet_gen downloads tweets from a user (if they haven't been downloaded already),
	#           reads them, and generates a tweet via a markov chain
	def tweet_gen(self, handle):
		# temporary tweet:
		tweet = "this is a tweet %d" % random.randint(0, 100)

		# download tweets (watching for private accts)
		if 'tweets' not in session:
			session.tweets = []

		if not session.tweets:
			print handle
			print "loading tweets..."

			try:
				session.tweets = get_all_tweets(handle)
			except tweepy.TweepError as e:
				print "error accessing tweets"
				print e
				return render.generated(handle, "", 0)

			print "found %d tweets" % len(session.tweets)
		
		# session.tweets = get_all_tweets(handle)

		# clean tweets
		session.tweets = self.tweet_cleaner(session.tweets)

		# for s in session.tweets:
		# 	print s

		# create markov bot
		mkbot = MarkovBot()

		# read tweets
		s = ""
		for current_tweet in session.tweets:
			s += current_tweet[0]
			s += " "
		# print s
		mkbot.read(s)

		# generate tweet
		try:
			tweet = mkbot.generate_text(random.randint(5, 21))
		except:
			return render.generated(handle, "", 2)

		# return render.generated(handle, tweet)
		return render.generated(handle, tweet, 1)

	def tweet_cleaner(self, tweets):
		newtweets = []
		for tweet in tweets:

			# # remove ellipses from tweets
			# if "..." in tweet:
			# 	tweet = tweet.replace("...", '')

			# remove fllwrs tweets
			if "// automatically checked by" not in tweet:
				# remove quoted tweets
				if "\"\"\"" not in tweet:
					# remove links if necessary
					s = ""
					if "http" in tweet:
						words = tweet.split()
						for word in words:
							if "http" not in word:
								s += word + " "
					else:
						s = tweet

					newtweets.append(s)

		return newtweets


if __name__ == "__main__":
	app.run()
