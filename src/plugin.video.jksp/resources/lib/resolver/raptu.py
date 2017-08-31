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


def resolve_video(url):
    html = fetch_url(url)
    r = re.search(r'<source src="(.+?)" type="video/mp4"', html)
    if r:
        return r.group(1)

    else:
        return None

def resolve(video_id):
    main_url = "https://www.rapidvideo.com/v/%s" % video_id

    main_html = fetch_url(main_url)
    if main_html is False:
        log_error("Failed to load main URL")
        return None

    qualities = re.findall(r'<a href="%s&q=(.+?)">' % main_url, main_html)
    videos = {}
    for quality in qualities:
        video = resolve_video(main_url + "&q=" + quality)
        if video:
            videos[quality] = video

    subs = {}
    s = re.finditer(r'<track src="<(/loadvtt\.php\?f=/srt/.+?)" kind="subtitles" .*label="(.+?)"', main_html)
    for r in re.finditer(r'<track src="(?P<U>/loadvtt\.php\?f=/srt/.+?)" kind="subtitles" .*label="(?P<L>.+?)"', main_html):
        subs[r.group(2)] = "https://www.rapidvideo.com" + r.group(1)

    return {'videos': videos,
            'subs': subs}


if __name__ == '__main__':
    movie_data = resolve(sys.argv[1])
    if movie_data:
        videos = movie_data['videos']
        for x in videos:
            print videos[x], x

        subs = movie_data['subs']
        for x in subs:
            print subs[x], x

    else:
        print("failed!")