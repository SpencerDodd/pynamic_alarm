# pynamic Alarm
This project is an alarm clock based off of Gmail Calendar integretion. 
The alarm system goes off dynamically based on events in your calendar. This was created 
## Installation
First thing to do is make sure you have all of the requirements grabbed
through your package manager.
```bash
pip install -r requirements.txt
```
Next, you need to grab your client_secret.json from google's api manager
credentials page [here](https://console.developers.google.com/apis/credentials?project=windy-planet-142714), which is placed into the project
directory (../pynamic_alarm/)

Then cd to src and start it up
```bash
cd src
python alarm.py
```