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
except ImportError:
    KODI_VERSION = 17


def fetch_url(url, headers={}):
    hdr = {'User-Agent': USER_AGENT}
    hdr.update(headers)

    if KODI_VERSION < 17:
        header_str = urllib2.quote("&".join(["%s=%s" % (n, v) for n, v in hdr.items()]))
        url = "http://jksp.webutu.com/resolver.for.kodi.16.1/getLINK.php?link=%s&headers=%s" % (url, header_str)

    try:
        req = urllib2.Request(url, headers=hdr)
        return urllib2.urlopen(req).read()

    except urllib2.URLError, e:
        xbmc.log("JKSP[%s]: %s" % (os.path.basename(__file__), str(e)), level=xbmc.LOGERROR)
        return False


def resolve(video_id):
    main_url = "https://www.raptu.com/?v=%s" % video_id

    main_html = fetch_url(main_url)
    if main_html is False:
        return False

    r = re.search(r'playerInstance\.on\(\'play\', function\(\) \{ \$\.get\( "(.+?)"\+canRunAds\);', main_html)
    if r is None:
        return False

    fetch_url(urlparse.urljoin("https://www.raptu.com", r.group(1) + "true"),
              headers={'X-Requested-With': "XMLHttpRequest", 'Referer': main_url})

    r = re.search(r'jwplayer\("home_video"\)\.setup\(.+?"sources": (\[.+?\]).+?\);', main_html)
    if r:
        video_sources = r.group(1)
        json_data = json.loads(video_sources)
        return dict([(x['label'], x['file']) for x in json_data if 'label' in x])

    else:
        return None


if __name__ == '__main__':
    movie_data = resolve(sys.argv[1])
    if movie_data:
        for x in movie_data:
            print movie_data[x], x

    else:
        print("failed!")