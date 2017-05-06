#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *
# *  Copyright (C) 2017      jk$p
# *  E-mail - jksp@protonmail.ch
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *


import getopt
import json
import os
import re
import sys
import time
import urllib
import urllib2

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"

TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_API_KEY = '34142515d9d23817496eeb4ff1d223d0'
ALL_MOVIE_PROPS = "account_states,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating"

global verbose
verbose = False

def log(message):
    if verbose:
        print(message)

def _tmdb_send_request(method, get={}, post=None):
    get['api_key'] = TMDB_API_KEY
    get = dict((k, v) for (k, v) in get.iteritems() if v)
    get = dict((k, unicode(v).encode('utf-8')) for (k, v) in get.iteritems())
    url = "%s%s?%s" % (TMDB_API_URL, method, urllib.urlencode(get))
    request = urllib2.Request(url=url,
                              data=post,
                              headers={'Accept': 'application/json',
                                       'Content-Type': 'application/json',
                                       'User-agent': USER_AGENT})
    try:
        response = urllib2.urlopen(request, timeout=10).read()

    except urllib2.HTTPError as err:
        return err.code

    return json.loads(response)


def tmdb_movie_info(tmdb_movie_id):
    params = {"append_to_response": ALL_MOVIE_PROPS,
              "language": "he",
              "include_image_language": "en,null,he"}
    response = _tmdb_send_request("movie/%s" % tmdb_movie_id,
                                  get=params)
    if isinstance(response, int):
        if response == 401:
            print("TMDB Error: Not authorized.")
        elif response == 404:
            print("TMDB Error: Movie '%s' not found." % tmdb_movie_id)
        else:
            print("TMDB Error: Unknown error.")
        return {}

    elif not response:
        print("TMDB Error: Could not get movie information")
        return {}

    return response

def tmdb_get_trailer(tmdb_movie_id, language="he"):
    params = {"language": language}
    response = _tmdb_send_request("movie/%s/videos" % tmdb_movie_id,
                                  get=params)
    if isinstance(response, int):
        if response == 401:
            print("TMDB Error: Not authorized.")
        elif response == 404:
            print("TMDB Error: Movie '%s' not found." % tmdb_movie_id)
        else:
            print("TMDB Error: Unknown error.")
        return {language: None}

    elif not response:
        print("TMDB Error: Could not get movie trailer")
        return {language: None}

    trailers = dict((v['iso_639_1'], v['key']) for v in response['results']
                    if v['site'] == "YouTube" and v['type'] == "Trailer")
    return {language: trailers.get(language, None)}

def imdb_id_to_tmdb(imdb_movie_id):
    params = {"external_source": "imdb_id"}
    response = _tmdb_send_request("find/%s" % imdb_movie_id,
                                  get=params)
    if isinstance(response, int):
        if response == 401:
            print("TMDB Error: Not authorized.")
        elif response == 404:
            print("TMDB Error: IMDB id '%s' not found." % imdb_movie_id)
        else:
            print("TMDB Error: Unknown error.")
        return None

    elif not response:
        print("TMDB Error: Could not translate IMDB id to TMDB id")
        return None

    if len(response['movie_results']):
        return response['movie_results'][0]['id']
    else:
        return None


def _http_send_request(url, headers={}):
    if not headers.has_key('User-Agent'):
        headers['User-Agent'] = USER_AGENT
    request = urllib2.Request(url=url,
                              headers=headers)
    try:
        return urllib2.urlopen(request, timeout=3).read()

    except urllib2.HTTPError as err:
        return err.code

def raptu_get_info(raptu_movie_id):
    response = _http_send_request("https://www.raptu.com/?v=%s" % raptu_movie_id)
    if isinstance(response, int):
        if response == 404:
            print("RAPTU Error: Movie '%s' not found." % raptu_movie_id)
        else:
            print("TMDB Error: Unknown error (%s)." % response)
        return None


    m = re.search(r'jwplayer\("home_video"\)\.setup\(.+?"sources": (\[.+?\]).+?\);', response)
    if m:
        json_data = json.loads(m.group(1))
        height = max([int(re.search("^(\d+)", x['label']).group(1)) for x in json_data if 'label' in x])
        return {"codec" : "h264",
                'height': height,
                'width' : {'1080': 1920, '720': 1280, '480': 640, '360': 640}.get(str(height), 0)}
    else:
        return {"codec": "h264"}


def parse_time(value):
    _re = re.compile(r'(\d+)\s*(hour|hr|h|min|sec)', re.I)
    seconds = sum(int(v) * {'h': 3600, 'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1}[u.lower()]
                  for v, u in _re.findall(value))
    return seconds


def imdb_get_info(imdb_movie_id):
    result = {}

    response = _http_send_request("http://www.imdb.com/title/%s" % imdb_movie_id)
    if isinstance(response, int):
        if response == 404:
            print("IMDB Error: Movie '%s' not found." % imdb_movie_id)
        else:
            print("IMDB Error: Unknown error (%s)." % response)
        return {}

    m = re.search('<time itemprop="duration" datetime="PT(\d+)M">', response)
    if m:
        result['duration'] = int(m.group(1))

    r = re.search('itemprop="ratingValue">([\d\.]+)<', response)
    v = re.search('itemprop="ratingCount">([\d,]+)<', response)
    if r and v:
        result.update({'rating': round(float(r.group(1)), 1),
                       'votes' : v.group(1)})
    return result


def add_movie(tmdb_movie_id, raptu_movie_id, db, youtube_trailer_id=None):
    log("Quering TMDB for movie '%s'." % tmdb_movie_id)
    response = tmdb_movie_info(tmdb_movie_id)
    if not  response:
        return None

    log("TMDB query finished successfully.")

    title =  response['title']

    if title in db['movies'] and db['movies'][title]['video_id'] != raptu_movie_id:
        print("Error: Another movie with the same name already exist, cannot add!")
        return None

    trailers = dict((v['iso_639_1'], v['key']) for v in  response['videos']['results']
                    if v['site'] == "YouTube" and v['type'] == "Trailer")
    trailer = youtube_trailer_id or trailers.get('he', None) or tmdb_get_trailer(tmdb_movie_id, "en").get('en', None)


    us_cert = [x for x in  response['releases'].get('countries', []) if x['iso_3166_1'] == "US"]
    if us_cert:
        mpaa = us_cert[0]['certification']
    elif  response['releases']['countries']:
        mpaa =  response['releases']['countries'][0]['certification']
    else:
        mpaa = ""

    movie_set =  response.get('belongs_to_collection')
    genres = " / ".join([i['name'] for i in  response['genres']])
    writers = " / ".join([i['name'] for i in  response['credits']['crew'] if i['department'] == "Writing"])
    directors = " / ".join([i['name'] for i in  response['credits']['crew'] if i['department'] == "Directing"])
    studios = " / ".join([i['name'] for i in  response['production_companies']])
    actors = [{'name': i['name'],
               'role': i['character'],
               'thumbnail': "https://image.tmdb.org/t/p/w640/%s" % i['profile_path'] if i['profile_path'] else "",
               'order': i['order']}
              for i in  response['credits']['cast']]
    actors = [dict((k, v) for (k, v) in a.iteritems() if v) for a in actors]

    imdb_info = None
    imdb_id = response.get('imdb_id', "")
    if imdb_id:
        log("Quering IMDB for rating, votes and duration of `%s`" % imdb_id)
        imdb_info = imdb_get_info(imdb_id)
        if imdb_info:
            log("IMDB query finished.")

        else:
            print("IMDB query failed, defaulting to TMDB rating and votes")

    else:
        print("Warning: TMDB movie '%s' had no IMDB id!" % tmdb_movie_id)

    rating = imdb_info['rating'] if imdb_info and 'rating' in imdb_info else round(response.get('vote_average', 0), 1)
    votes = imdb_info['votes'] if imdb_info and 'votes' in imdb_info else response.get('vote_count', 0)
    duration = (imdb_info['duration'] if imdb_info and 'duration' in imdb_info else response.get('runtime', 0) or 0) * 60

    if response['production_countries']:
        country = response['production_countries'][0]["name"]
    else:
        country = response.get('original_language', "")

    video_info = {'genre'        : genres,
                  'country'      : country,
                  'year'         : int(response.get('release_date', "0")[:4]),
                  'rating'       : rating,
                  'director'     : directors,
                  'mpaa'         : mpaa,
                  'plot'         : response.get('overview', ""),
                  'originaltitle': response.get('original_title', ""),
                  'duration'     : duration,
                  'studio'       : studios,
                  'writer'       : writers,
                  'premiered'    : response.get('release_date', ""),
                  'set'          : movie_set.get("name") if movie_set else "",
                  'setid'        : movie_set.get("id") if movie_set else "",
                  'imdbnumber'   : imdb_id,
                  'votes'        : votes,
                  'dateadded'    : time.strftime("%Y-%m-%d %H:%M:%S"),
                  'trailer'      : trailer}
    video_info = dict((k, v) for (k, v) in video_info.iteritems() if v)

    log("Quering Raptu for stream info of movie '%s'." % raptu_movie_id)
    stream_info = raptu_get_info(raptu_movie_id)
    if stream_info is None:
        return
    log("Raptu query finished.")

    movie = {'video_id'     : raptu_movie_id,
             'thumb'        : "https://image.tmdb.org/t/p/original/%s" % response.get('poster_path'),
             'fanart'       : "https://image.tmdb.org/t/p/original/%s" % response.get('backdrop_path'),
             'video_info'   : video_info,
             'actors'       : actors,
             'stream_info'  : stream_info}

    log("Adding movie to DB.")
    db['movies'][title] = movie

    return db

def usage():
    print("")
    print("Usage: %s [OPTION]... <db_file.json> <raptu_movie_id> <movie_id>" % os.path.basename(sys.argv[0]))
    print("")
    print("Options:")
    print("  -h,  --help                 print this help")
    print("  -o,  --output=FILE          write output to FILE (default update source file)")
    print("  -p,  --pretty               write output in human readable format")
    print("  -t,  --trailer=ID           specify trailer YouTube video ID")
    print("  -v,  --verbose              be verbose")
    print("")
    print("Note: movie_id can be TMDB id or IMDB id.")


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:pt:v", ["help", "output=", "pretty", "trailer=", "verbose"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    out_file = None
    pretty = None
    youtube_trailer_id = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            log("Output will be saved to '%s'." % a)
            out_file = a
        elif o in ("-p", "--pretty"):
            log("Saving in human readable text")
            pretty = 4
        elif o in ("-t", "--trailer"):
            youtube_trailer_id = a
        elif o in ("-v", "--verbose"):
            verbose = True
        else:
            assert False, "unhandled option"

    if len(args) != 3:
        usage()
        sys.exit(2)

    db_file = args[0]
    raptu_movie_id = args[1]
    movie_id = args[2]
    out_file = out_file or db_file

    if not os.path.isfile(db_file):
        log("Warning: file `%s` does not exist, creating a new DB" % db_file)
        j = '{"movies":{}}'
    else:
        log("Loading file '%s' into memory." % db_file)
        with open(db_file, "r") as f:
            j = f.read()

    db = json.loads(j)
    log("File loaded succesfully.")

    if movie_id.isdigit():
        tmdb_movie_id = movie_id

    elif movie_id.startswith("tt") and movie_id[2:].isdigit():
        log("Translating IMDB id '%s' to TMDB id." % movie_id)
        tmdb_movie_id = imdb_id_to_tmdb(movie_id)
        if tmdb_movie_id is None:
            sys.exit(2)
        log("IMDB id '%s' it TMDB is '%s'." % (movie_id, tmdb_movie_id))

    else:
        print("Error: invalid movie_id!")
        sys.exit(2)

    print("Adding %s" % movie_id)
    if add_movie(tmdb_movie_id, raptu_movie_id, db, youtube_trailer_id):
        log("Saving DB to '%s'." % out_file)
        with open(out_file, "wb") as f:
            f.write(json.dumps(db, ensure_ascii=False, indent=pretty).encode('utf8'))
        log("DB saved successfully.")

        print("Done.")


