import json
import os
import re
import sys
import urllib2
import urlparse

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"

try:
    import xbmc

    KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split('.', 1)[0])
    KODI = True
except ImportError:
    KODI_VERSION = 17
    KODI = False


def log_error(message):
    if KODI:
        xbmc.log("JKSP[%s]: %s" % (os.path.basename(__file__), message), level=xbmc.LOGERROR)
    else:
        print("JKSP[%s]: %s" % (os.path.basename(__file__), message))


def fetch_url(url, headers={}, direct=False, size=None):
    hdr = {'User-Agent': USER_AGENT}
    hdr.update(headers)

    if KODI_VERSION < 17 and direct is False:
        header_str = urllib2.quote("&".join(["%s=%s" % (n, v) for n, v in hdr.items()]))
        url = "http://jksp.webutu.com/resolver.for.kodi.16.1/getLINK.php?link=%s&headers=%s" % (url, header_str)

    try:
        req = urllib2.Request(url, headers=hdr)
        return urllib2.urlopen(req).read(size)

    except urllib2.URLError, e:
        log_error(str(e))
        return False


def resolve(video_id):
    main_url = "https://www.raptu.com/?v=%s" % video_id

    main_html = fetch_url(main_url)
    if main_html is False:
        log_error("Failed to load main URL")
        return False

    r = re.search(r'\$\.getJSON\("(.+?)"\+canRunAds', main_html)
    if r is None:
        log_error("Player URL not found")
        return False

    player_url = urlparse.urljoin("https://www.raptu.com", r.group(1) + "true")
    print player_url

    r = re.search(r'jwplayer\("home_video"\)\.setup\(.+?"sources": (\[.+?\]).+?\);', main_html)
    if r:
        video_sources = r.group(1)
        json_data = json.loads(video_sources)
        videos = [(x['label'], x['file']) for x in json_data if 'label' in x]

        #        fetch_url(videos[0][1], direct=True, size=1* 1024 * 1024)
        #        print fetch_url(player_url, headers={'X-Requested-With': "XMLHttpRequest", 'Referer': main_url})

        return dict(videos)

    else:
        log_error("Video URL not found")
        return None


if __name__ == '__main__':
    movie_data = resolve(sys.argv[1])
    if movie_data:
        for x in movie_data:
            print movie_data[x], x

    else:
        print("failed!")