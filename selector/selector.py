from bottle import Bottle, run
import eyeD3
import json
import os
import random
import redis
import time

SPINS_ZSET_KEY = 'spins'
LAST_ID_KEY = 'last_station_id'
LAST_ROTATION_SPIN_KEY = 'last_rotation_spin'

execfile('/etc/tuubz/selector.conf')

class NoFreshSongsError(Exception):
    pass

def build_metadata(tag):
    metadata = []
    metadata.append(str(tag.getArtist()))
    metadata.append(str(tag.getTitle()))
    if (tag.getYear()):
        metadata.append(str(tag.getYear()))
    return " | ".join(metadata)

def fresh_song(songs):
    available_songs = len(songs)
    fresh = False
    while not fresh:
        if available_songs == 0:
            raise NoFreshSongsError
        song = random.choice(songs)
        if test_for_tags(song):
            tag = eyeD3.Mp3AudioFile(song).getTag()
            artist = str(tag.getArtist())
            try:
                last_spin = int(redis_server.zscore(SPINS_ZSET_KEY,artist.lower()))
            except:
                last_spin = 0
            try:
                minutes_since_last_spin = int(time.time() - last_spin) / 60
                print "{} minutes since last spin of {}".format(
                        minutes_since_last_spin, artist.lower())
                if minutes_since_last_spin > REPETITION_MINUTES:
                    fresh = True
                else:
                    available_songs -= 1
                    fresh = False
                    print u'{} is stale, skipping.'.format(artist)
                    artist = ""
            except KeyError:
                fresh = True
        else:
            pass

    metadata = build_metadata(tag)
    result = {"filename": song,
              "metadata" : metadata}
    redis_server.zadd(SPINS_ZSET_KEY, int(time.time()), artist.lower())
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


def prime_rotation_key():
    redis_server.set(LAST_ROTATION_SPIN_KEY, '0')


def prime_spins_key():
    redis_server.zadd(SPINS_ZSET_KEY, int(time.time()), 'STARTUP')
    return None


def prime_station_id_key():
    redis_server.set(LAST_ID_KEY, '0')
    return None


global redis_server

redis_server = redis.StrictRedis(host=REDIS_SERVER['host'],
                                 port=REDIS_SERVER['port'],
                                 db=REDIS_SERVER['db'])
if not redis_server.exists(LAST_ID_KEY):
    prime_station_id_key()

if not redis_server.exists(SPINS_ZSET_KEY):
    prime_spins_key()

if not redis_server.exists(LAST_ROTATION_SPIN_KEY):
    prime_rotation_key()

station_ids = [os.path.join(STATION_ID_DIR, f) for f in os.listdir(STATION_ID_DIR)]
catalog = [os.path.join(MUSIC_DIR_CATALOG, f) for f in
        os.listdir(MUSIC_DIR_CATALOG)]
rotation = [os.path.join(MUSIC_DIR_ROTATION, f) for f in
        os.listdir(MUSIC_DIR_ROTATION)]

app = Bottle()
@app.route('/select')
def select():
    while True:
        id_played = int(redis_server.get(LAST_ID_KEY))
        if (int(time.time()) - id_played) > (60 * ID_MINUTES):
            print "play an ID"
            redis_server.set(LAST_ID_KEY,int(time.time()))
            return json.dumps(random_id(station_ids), indent=True)
        else:
            print "play a song"
            if int(time.time()) - int(redis_server.get(LAST_ROTATION_SPIN_KEY)) > (60 *
                    ROTATION_SPIN_MINUTES):
                redis_server.set(LAST_ROTATION_SPIN_KEY,int(time.time()))
                return json.dumps(fresh_song(rotation), indent=True)
            else:
                return json.dumps(fresh_song(catalog), indent=True)

run(app, host=HOST_IP, port=HOST_PORT)
