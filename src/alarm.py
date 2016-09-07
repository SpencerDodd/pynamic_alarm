"""
Alarm app that pulls from all planning / calendar sources and wakes you up 
dynamically and accordingly.

On alarm:
	play alarm tone
	text to speech name of calendar event
"""

import os
import json
import time
import pydub # for splicing alarm and alert audio
import pyttsx
import datetime
import httplib2
import threading
import subprocess
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
#from __future__ import print_function

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

### ===========================================================================
### ==== DATA STRUCTURES ======================================================
### ===========================================================================


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
		flow = client.flow_from_clientsecrets(os.path.join(home_dir, CLIENT_SECRET_FILE), SCOPES)
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
	print('Getting the upcoming 10 events')
	eventsResult = service.events().list(
		calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		print(start, event['summary'])

def text_to_speech(text):
	"""Speaks the given text as audio on the device running the alarm app.
	"""
	message = "{}".format(text)
	
	engine = pyttsx.init()
	engine.say(message)
	engine.runAndWait()
	
	# sleep for as long as it would take to say the text
	print "speaking"
	time.sleep(len(text) / 5)
	print "done speaking"
	return 0

def main():
	threads = []
	comments = [
		"This is just a test test test test test"
	]
	for i in comments:
		t = threading.Thread(target=text_to_speech, args=(i,))
		t.start()

	while True:
		time.sleep(1)
		print "running"


if __name__ == '__main__':
	main()
















