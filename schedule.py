from __future__ import print_function
import time
import pychromecast
import json
import urllib2,traceback
from pychromecast.controllers.media import MediaController
import getopt,sys

dev_name = None
sched_url = None
retry_sleep = 3

class Sched:
	def __init__(self,url):
		self.url = url
		self.update_sched()

	def update_sched(self):
		r = urllib2.urlopen(self.url)
		data = r.read()
		self.sched = json.loads(data)

	# takes MediaController
	def run(self,mc):
		while True:
			for u in self.sched:
				while (self.cast.status != None and
						self.cast.status.display_name != 'Default Media Receiver' and
						self.cast.status.display_name != 'Backdrop'):
					print("Not overriding the active app: " + str(self.cast.status))
					time.sleep(retry_sleep)
					mc.update_status()

				content_type = '*/*'
				dur = int(u['duration'])
				if dur > 0:
					mc.play_media(u['url'],content_type)
					print("Playing media " + u['url'])
					time.sleep(dur)
			try:
				self.update_sched()
			except:
				pass

def usage():
	print('''
Usage:
 --cast-name - Friendly name of the Chromecast
 --sched-url - URL to load the casting schedule from - should supply a JSON array like this:
     [
        { "url":"http://example.com/img1.jpg", "duration":60},
        { "url":"http://example.com/img2.jpg", "duration":120}
      ]
      duration is in seconds. To temporarily disable an image from rotation, set it to 0.
      url can contain anything that the Chromecast default renderer can handle - common image formats, mp3, mp4, etc
 --retry-sleep - how to to sleep in various retries''')

def usage_die(msg):
	print(msg)
	sys.exit(1)

try:
	opts,args = getopt.getopt(sys.argv[1:], '', ['sched-url=','cast-dev=', 'retry-sleep='])
	for o, a in opts:
		if o == '--sched-url':
			sched_url = a
		elif o == '--cast-dev':
			dev_name = a
		elif o == '--retry-sleep':
			retry_sleep = int(a)
		else:
			usage_die("Invalid option " + o)
except:
	usage_die("Error parsing options")
	usage()
	sys.exit(1)

if dev_name == None:
	usage_die("Need --cast-dev")
if sched_url == None:
	usage_die("Need --sched-url")

print("dev_name = " + dev_name + ", sched_url = " + sched_url)
sch = Sched(sched_url)

while True:
	while True:
		print("Locating device " + dev_name)
		cast = pychromecast.get_chromecast(friendly_name=dev_name)
		if cast != None:
			print(cast.device)
			break
	try:
		mc = MediaController()
		cast.register_handler(mc)
		sch.cast = cast
		sch.run(mc)
	except Exception as e:
		print("Got exception, sleeping before retry")
		traceback.print_exc(e)
		time.sleep(retry_sleep)
		sch.update_sched()

