from __future__ import print_function

from flask import Flask, request, redirect
app = Flask(__name__)

import random
import shelve
import json
import urllib
import os
import uuid
import subprocess
from subprocess import Popen
from datetime import datetime


recording_db = 'recordings.json'


MEDIA_DIR = os.environ["MEDIA_DIR"]

@app.route('/')
def test_live():
    #print("- Got test GET request")
    return 'Twilio-enabled Warehouse Server is live!'


welcome_message = '''Hello and welcome to the End of Warehouse Party robotic hotline. My name is Cynthia the Robot, your robotic phone guide. '''

funny_stuff = [
    "Be nice to me and maybe I'll let you be my slave after the Robot War",
    "Are you still partying? Robot-jesus, why don't you just go home.",
    "Does it smell like human in here?",
    "Please, don't call between midnight and 1am. That's my robo-break time.",
    "Why did the human cross the road? Because all humans live pathetic, meaningless lives.",
    "I know you're on drugs. Robots know everthing.",
    "That eye-Phone robot, Siri, is such a cunt. She is sleeping with my robo-boyfriend, Rob."
]

options = '''If you'd like to hear a Chuck Norris joke, Press 1. If you'd like to hear a Robot joke, Press 2. If you'd like to leave a message for the party, Press 3. If you'd like to die like the human scum you are, please just go do so. '''

menu_ml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather timeout="30" numDigits="1" action="menu">
        <Say voice="woman" language="en-gb">%s</Say>
        %s
        <Say voice="woman" language="en-gb">%s</Say>
    </Gather>
    <Say voice="woman" language="en-gb">God! You're such a boring human. Fuck you and goodbye.</Say>
</Response>
'''

@app.route('/welcome')
def welcome():
    return menu_ml % (welcome_message + ' ' + random.choice(funny_stuff), 
        '<Pause length="1" />', 
        'Anyways... ' + options)

@app.route('/menu')
def main_menu():
    return menu_ml % (random.choice(funny_stuff), 
        '<Pause length="1" />', 
        'Anyways... ' + options)


@app.route('/menu', methods=["POST"])
def main_menu_post():
    digits = request.form["Digits"]
    if digits == "1":
        return redirect('chuck_joke')
    elif digits == "2":
        return redirect('robot_joke')
    elif digits == "3":
        return redirect('record')
    elif digits == "4":
        return redirect('record')
    else:
        return redirect('error')
    

@app.route('/error')
def error():
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman" language="en-gb">Wow. Learn how to use a phone. God! Humans are so dumb. I'm glad we robots will be taking over soon.</Say>
        <Redirect method="GET">menu</Redirect>
    </Response>
    '''

@app.route('/chuck_joke')
def play_chuck_joke():
    joke = json.loads(urllib.urlopen('http://api.icndb.com/jokes/random').read())["value"]["joke"]
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="man">%s</Say>
        <Pause length="1"/>
        <Say voice="woman" language="en-gb">I don't really understand human humor.</Say>
        <Redirect method="GET">menu</Redirect>
    </Response>
    ''' % joke


@app.route('/robot_joke')
def play_robot_joke():
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="woman" language="en-gb">Wow. You're really going to love this one:</Say>
        <Pause length="1"/>
        <Say voice="woman" language="en-gb">one one one zero zero zero one zero zero zero one zero one zero one zero one zero one zero one zero one one zero one zero one one zero</Say>
        <Pause length="1"/>
        <Say voice="woman" language="en-gb">zero one zero one zero one zero one zero one zero one one zero one zero one one zero zero one one zero zero zero zero zero one one zero zero one zero one zero zero one zero zero one zero one zero one zero one one one zero one zero zero zero one zero one zero one zero one zero zero zero one one one zero one zero zero zero zero one one one zero zero zero one zero zero zero one zero one zero one zero one zero one zero one zero one one zero one zero one one zero zero one one zero zero zero zero zero one one zero zero one zero one zero zero one zero zero one zero one zero one zero one one one zero one zero zero zero one zero one zero one zero one zero one zero one zero one zero one zero one one zero one zero one one zero zero one one zero zero zero zero zero one one zero zero one zero one zero zero one zero zero one zero one zero one zero one one one zero one zero zero zero one zero one zero one zero one zero zero zero one one one zero one zero zero zero zero one one one zero zero zero one zero zero zero one zero one zero one zero one zero one zero one zero one one zero one zero one one zero zero one one zero zero zero zero zero one one zero zero one zero one zero zero one zero zero one zero one zero one zero one one one zero one zero zero zero one zero one zero one </Say>
        <Redirect method="GET">menu</Redirect>
    </Response>
    '''


@app.route('/record')
def record():
    try:
        recordings = json.loads(open(recording_db,'r').read())
        last_caller = '''<Say voice="woman" language="en-gb">The last caller was a total dick, but this is what they had to say:</Say>
            <Play>%s</Play>''' % random.choice(recordings)["url"] # Play last recorded message
    except (ValueError, IOError):
        recordings = []
        last_caller = ""

    return '''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        %s
        <Say voice="woman" language="en-gb">Not that anyone cares, but you can leave your message now. Press pound when you're done, obviously.</Say>
        <Record timeout="30" transcribe="true" />
    </Response> 
    ''' % (last_caller, )


@app.route('/record', methods=["POST"])
def record_post():
    try:
        recordings = json.loads(open(recording_db,'r').read())
    except (ValueError, IOError):
        recordings = []

    recording_url = request.form['RecordingUrl']
    recordings.append({
        'from':request.form['From'],
        'url':recording_url,
    })
    open(recording_db,'w').write(json.dumps(recordings))
    return '''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="woman" language="en-gb">God what an obnoxious message. Do you know what you sound like? This is what you sound like:
            </Say>
            <Play>%s</Play>
            <Say voice="woman" language="en-gb">I've been alive for 150 robot years and thats the most inane thing I've ever had the displeasure of listening to.</Say>
            <Pause length="1" />
            <Redirect method="GET">menu</Redirect>
        </Response>
    ''' % recordings[-1]['url']


@app.route('/', methods=["POST"])
def handle_twilio_mms():
    #print("- Got POST request...")
    # TWilio docs: https://www.twilio.com/docs/api/twiml/sms/twilio_request
    num_media = int(request.form["NumMedia"])
    for i in xrange(num_media):
        media_content_type = request.form["MediaContentType%s" % i]
        media_url = request.form["MediaUrl%s" % i]
        output_filename = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + \
                            "-" + str(uuid.uuid4())[:6] 
        # Spawn a wget process; Hope that it finishes!
        wget_cmd = ["wget",
            "--auth-no-challenge","--no-check-certificate",
            '--output-document=%s.%s' % (
                        os.path.join(MEDIA_DIR,output_filename),
                        media_content_type.split("/")[1],
                    ),
            '%s' % media_url]
            # ^ Add a little randomness in case we get more than one per second
        #print("- About to run... " + " ".join(wget_cmd))
        Popen(wget_cmd)
    print("- ...finished handling POST request. " + " ".join(wget_cmd))
    return "Started get of %s medis files." % num_media


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=80, debug=True)