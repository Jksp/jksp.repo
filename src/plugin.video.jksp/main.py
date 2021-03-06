# -*- coding: utf-8 -*-
# Module: default
# Author: Jk$p
# Email: Jksp@protonmail.ch
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import os
import urllib2

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json

from urllib import urlencode
from urlparse import parse_qsl

_url = sys.argv[0]
_handle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.jksp')
sys.path = [os.path.join(settings.getAddonInfo('path'), "resources", "lib", "resolver")] + sys.path

from raptu import resolve

KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split('.', 1)[0])
CATEGORIES = None
VIDEOS = {"categories": {}}


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def log(msg, level=xbmc.LOGERROR):
    xbmc.log ("JKSP[%s]: %s" %(os.path.basename(__file__), msg), level=level)

def load_categories():
    try:
        f = urllib2.urlopen('https://raw.githubusercontent.com/Jksp/jksp.repo/master/db/menu.json')

    except urllib2.URLError, e:
        log(str(e))
        return []

    return json.loads(f.read())


def load_movies(category):
    try:
        f = urllib2.urlopen(CATEGORIES['categories'][category.decode("UTF8")]['url'])

    except urllib2.URLError, e:
        log(str(e))
        return []

    return json.loads(f.read())['movies']


def get_categories():
    return CATEGORIES["categories"].iterkeys()


def list_categories():
    categories = get_categories()

    for category in categories:
        list_item = xbmcgui.ListItem(label=category)
        list_item.setArt({'thumb': CATEGORIES["categories"][category]['thumb'],
                          'fanart': CATEGORIES["categories"][category]['fanart']})
        list_item.setInfo('video', {'title': category, 'genre': category})
        url = get_url(action='listing', category=category.encode("UTF8"))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


def list_videos(category):
    videos = load_movies(category)

    for video in videos.iteritems():
        list_item = xbmcgui.ListItem(label=video[0].encode("UTF8"))
        list_item.setInfo('video', {'title': video[0].encode("UTF8"), 'mediatype': "movie"})
        list_item.setArt({'thumb': video[1]['thumb'], 'fanart': video[1]['fanart'], 'icon': video[1]['thumb'], 'poster': video[1]['thumb']})
        list_item.addStreamInfo('video', video[1]['stream_info'])
        video_info = video[1]['video_info']
        if 'trailer' in video_info:
            video_info['trailer'] = "plugin://plugin.video.youtube?&action=play_video&videoid=%s" % video_info['trailer']
        list_item.setInfo('video', video_info)
        if KODI_VERSION >= 17:
            list_item.setCast(video[1]['actors'])
        else:
            list_item.setInfo('video', {'castandrole': [(_a['name'], _a.get('role', "")) for _a in video[1]['actors']]})
        #list_item.addContextMenuItems([(xbmc.getLocalizedString(33029).encode('utf-8'), 'Action(Info)')], replaceItems=True)
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=video[1]['video_id'])
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.setContent(_handle, "movies")
    xbmcplugin.endOfDirectory(_handle)

def play_video(video):
    video_data = resolve(video)

    videos = video_data['videos']
    subs = video_data['subs']

    qualities = sorted([_x.encode("UTF8") for _x in videos.keys()], key=lambda _q: int(filter(str.isdigit, _q)))
    dialog = xbmcgui.Dialog()

    ret = dialog.select("Choose quality to play", qualities)
    if ret != -1:
        video_url = videos[qualities[ret]]

        play_item = xbmcgui.ListItem(path=videos[qualities[ret]])
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

        if subs:        
            player = xbmc.Player()

            for _i in xrange(10):
                if player.isPlaying():
                    player.setSubtitles(subs.values()[0])
                    break

                elif xbmc.abortRequested:
                    break

                xbmc.sleep(1000)

            else:
                log("Wait for play timeout")

            del player


def router(paramstring):
    params = dict(parse_qsl(paramstring))


    global CATEGORIES
    CATEGORIES = load_categories()


    if params:
        if params['action'] == 'listing':
            list_videos(params['category'])

        elif params['action'] == 'play':
            play_video(params['video'])

        else:

            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])