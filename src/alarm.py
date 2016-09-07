"""
Alarm app that pulls from all planning / calendar sources and wakes you up 
dynamically and accordingly.

On alarm:
	play alarm tone
	text to speech name of calendar event
"""

import os
import sys
import json
import time
import pyttsx
import datetime
import httplib2
import threading
import subprocess
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

### ===========================================================================
### ==== CREDENTIAL VARIABLES =================================================
### ===========================================================================
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Pynamic Alarm'
BASE_DIR = os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep)

### ===========================================================================
### ==== APPLICATION VARIABLES ================================================
### ===========================================================================
alarm_cutoff_time = 4 # Earliest time an alarmed event can start (24hr clock)
alarms = {} # dict: key = time of alarm, value = AlarmAlert for event
timezone_adjustments = { # adjustments to utc time
	"est" : -4,
}
current_timezone = "est"

### ===========================================================================
### ==== DATA STRUCTURES ======================================================
### ===========================================================================
class AlarmAlert:

	def __init__(self, alert_title, alert_time, alert_location):
		self.alert_title = alert_title
		self.alert_time = alert_time
		self.alert_location = alert_location

		# non-input
		self.triggered = False
		self.acknowledged = False

	def alarm_alert(self):
		"""Alerts for an alarm.

		Includes playing alarm tones and text to speech of the alarm title for
		the alerting event.

		Plays until it is acknowledged (stopped)
		"""
		print "Alerting for {} at {}".format(self.alert_title, self.alert_time)
		message = "{}".format(self.alert_title)
	
		# Alarm noise
		alarm_location = os.path.join(BASE_DIR, "static/alarm.wav")
		subprocess.Popen(["afplay", alarm_location])
		time.sleep(5)

		# Text to speech
		engine = pyttsx.init()
		engine.say(message)
		engine.runAndWait()
		
		# sleep for as long as it would take to say the text
		print "speaking"
		time.sleep(len(message) / 5)
		print "done speaking"
		return

	def run(self):
		if not self.triggered:
			t = threading.Thread(target=self.alarm_alert)
			t.start()
			self.triggered = True

	### ==== TEST METHODS =============================
	def test_alert(self):
		print "="*30
		print "Alerting for {} at {}".format(self.alert_title, self.alert_time)
		print "="*30

	def test_run(self):
		t = threading.Thread(target=self.test_alert)
		t.start()
	### ===============================================

### ===========================================================================
### ==== METHODS ==============================================================
### ===========================================================================
def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser(BASE_DIR)
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'calendar-python-alarm.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(
			os.path.join(home_dir, CLIENT_SECRET_FILE), 
			SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def get_upcoming_events():
	"""Creates a Google Calendar API service object and outputs a list of the 
	next 10 events on the user's calendar.
	"""
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	print('Searching for upcoming events ...')
	eventsResult = service.events().list(
		calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	
	return events
	

def update_alarms():
	""" This method gets the next 10 events, or the next two days worth of
	events (whichever set is larger). It then compares these events to existing
	alarms (based on timestamp and name). If there are new events that are not
	in the current alarm set, a new AlarmAlert object is created and added to
	the alarm set. 

	Previously alerted events are also removed from the alarm set. TODO
	"""
	events = get_upcoming_events()

	for event in events:
		event_name = event.get('summary')
		event_time = event.get('start').get('dateTime')
		event_location = event.get('location')

		# if there isn't an alarm at this event's time, add it
		if event_time not in alarms.keys() and not_before_cutoff(event_time):
			create_alarm(event_name, event_time, event_location)
			
def not_before_cutoff(event_time):
	""" This method checks to make sure that an event's time is not before
	the cutoff time specified in our variables section.

	Returns true if the event time is acceptable (after cutoff)
	Returns false if the event time is unacceptable (before cutoff)
	"""
	return True

def create_alarm(event_name, event_time, event_location):
	""" This method creates a new alarm event with the given values.
	"""
	print "New event alarm:"
	print "	Name: {}".format(event_name)
	print "	Time: {}".format(event_time)
	print "	Location: {}".format(event_location)
	new_alert = AlarmAlert(event_name, event_time, event_location)
	alarms[event_time] = new_alert

def check_alarms():
	""" This method checks the current timestamp against all of the current
	alarms (+/- 30 seconds). If there is a match (timestamp overlap), the
	alarm with overlap to current time is triggered (.run()).
	"""
	current_time = datetime.datetime.utcnow().isoformat() + 'Z'
	for alarm_time in alarms:
		f_current_time = format_time(current_time, 'utcnow')
		f_alarm_time = format_time(alarm_time, 'google')

		if f_current_time == f_alarm_time:
			alarms[alarm_time].run()


def format_time(timestring, time_format):
	""" Formats a given timestring into YYYY-MM-DD-MM-HH according to
	the time_format field that is given.
	"""
	if time_format == 'utcnow':
		year = timestring[:4]
		month = timestring[5:7]
		day = timestring[8:10]
		hour = str(
			int(timestring[11:13]) + timezone_adjustments[current_timezone]
			)
		minute = timestring[14:16]

		return "{}-{}-{}-{}-{}".format(year, month, day, hour, minute)

	elif time_format == 'google':
		year = timestring[:4]
		month = timestring[5:7]
		day = timestring[8:10]
		hour = timestring[11:13]
		minute = timestring[14:16]

		return "{}-{}-{}-{}-{}".format(year, month, day, hour, minute)


def main():
	while True:
		update_alarms()
		check_alarms()
		time.sleep(1)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print "\n\nInterrupted. Exiting ...\n"
		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)
















