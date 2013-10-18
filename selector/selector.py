from bottle import Bottle, run
import eyeD3
import json
import os
import random
import time

DEFAULT_METADATA = "http://tuu.bz"
ID_MINUTES = 10
STATION_ID_DIR = '/srv/mp3/station_id'
MUSIC_DIR = '/srv/mp3/music'
HOST_IP = '192.168.122.108'
HOST_PORT = '8080'
REPETITION_MINUTES = 60

def build_metadata(tag):
    metadata = []
    metadata.append(str(tag.getArtist()))
    metadata.append(str(tag.getTitle()))
    metadata.append(str(tag.getYear()))
    return " | ".join(metadata)

def fresh_song(songs):
    global spin
    fresh = False
    while not fresh:
        song = random.choice(songs)
        if test_for_tags(song):
            tag = eyeD3.Mp3AudioFile(song).getTag()
            try:
                if int(time.time() - spin[tag.getArtist()]) > \
                (REPETITION_MINUTES * 60):
                    fresh = True
                else:
                    print u'{} is stale, skipping.'.format(tag.getArtist())
            except KeyError:
                fresh = True
        else:
            break

    metadata = build_metadata(tag)
    result = {"filename": song,
              "metadata" : metadata}
    spin[tag.getArtist()] = int(time.time())
    return result


def random_id(ids):
    result = {"filename" : random.choice(station_ids),
            "metadata" : DEFAULT_METADATA}
    return result


def test_for_tags(fname):
    try:
        mp3 = eyeD3.Mp3AudioFile(fname)
    except eyeD3.tag.InvalidAudioFormatException:
        return False
    except eyeD3.tag.TagException:
        return False
    except TypeError:
        return False
    except UnicodeDecodeError:
        return False

    tag = mp3.getTag()

    if tag == None:
        return False

    print "found tag"
    return True

global id_played
global spin
id_played = 0
spin = {}

station_ids = [os.path.join(STATION_ID_DIR, f) for f in os.listdir(STATION_ID_DIR)]
music = [os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR)]

app = Bottle()
@app.route('/select')
def select():
    global id_played 
    while True:
        if (int(time.time()) - id_played) > (60 * ID_MINUTES):
            print "play an ID"
            id_played = int(time.time())
            return json.dumps(random_id(station_ids), indent=True)
        else:
            print "play a song"
            return json.dumps(fresh_song(music), indent=True)

run(app, host=HOST_IP, port=HOST_PORT)
