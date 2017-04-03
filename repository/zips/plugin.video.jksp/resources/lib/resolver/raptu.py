import json
import os
import re
import sys
import urllib2

import xbmc


def resolve(video_id):

    kodi_version = int(xbmc.getInfoLabel("System.BuildVersion").split('.', 1)[0])

    if kodi_version < 17:
        url = "http://jksp.webutu.com/resolver.for.kodi.16.1/getLINK.php?link=https://www.raptu.com/?v=%s" % video_id

    else:
        url = "https://www.raptu.com/?v=%s" % video_id

    try:
        req = urllib2.Request(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"})
        html = urllib2.urlopen(req).read()

    except urllib2.URLError, e:
        xbmc.log ("JKSP[%s]: %s" %(os.path.basename(__file__), str(e)), level=xbmc.LOGERROR)
        return False

    r = re.search('jwplayer\("home_video"\)\.setup\(.+?"sources": (\[.+?\]).+?\);', html)
    if r:
        video_sources = r.group(1)
        json_data = json.loads(video_sources)
        return dict([(x['label'],x['file']) for x in json_data if 'label'in x])

    else:
        return None

if __name__ == '__main__':
    movie_data = resolve(sys.argv[1])
    if movie_data:
        for x in movie_data:
            print movie_data[x],x

    else:
        print("failed!")
