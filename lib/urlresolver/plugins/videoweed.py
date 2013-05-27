"""
    urlresolver XBMC Addon
    Copyright (C) 2011 t0mm0

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import urllib2
import os

from t0mm0.common.net import Net
from urlresolver import common
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
import xbmcgui


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class VideoweedResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "videoweed.es"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)

        #grab stream details
        try:
            html = self.net.http_GET(web_url).content

            r = re.search('flashvars.domain="(.+?)".*flashvars.file="(.+?)".*' +
                          'flashvars.filekey="(.+?)"', html, re.DOTALL)
            #use api to find stream address
            if r:
                domain, fileid, filekey = r.groups()
                api_call = ('%s/api/player.api.php?user=undefined&codes=1&file=%s' +
                            '&pass=undefined&key=%s') % (domain, fileid, filekey)
                api_html = self.net.http_GET(api_call).content
                rapi = re.search('url=(.+?)&title=', api_html)
                if rapi:
                    return rapi.group(1)
            return self.unresolvable()

        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            return self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** Videoweed Error occured: %s' % e)
            return self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return 'http://www.videoweed.es/file/%s' % media_id


    def get_host_and_id(self, url):
        r = re.search('//(?:embed.)?(.+?)/(?:video/|embed.php\?v=|file/)' +
                      '([0-9a-z]+)', url)
        if r:
            return r.groups()
        return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match('http://(www.|embed.)?videoweed.(?:es|com)/(video/|file|embed.php\?|file/)' +
                        '(?:[0-9a-z]+|width)', url) or 'videoweed' in host

