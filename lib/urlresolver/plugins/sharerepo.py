"""
Sharerepo urlresolver plugin
Copyright (C) 2013 Vinnydude

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import os
import urllib2

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
import xbmcgui
from urlresolver import common

from lib import jsunpack


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class SharerepoResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "sharerepo"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        try:
            dialog = xbmcgui.DialogProgress()
            dialog.create('Resolving', 'Resolving Sharerepo Link...')
            dialog.update(0)
            url = self.get_url(host, media_id)
            html = self.net.http_GET(url).content

            data = {}
            r = re.findall(r'type="(?:hidden|submit)?" name="(.+?)"\s* value="?(.+?)">', html)
            for name, value in r:
                data[name] = value

            html = self.net.http_POST(url, data).content

            dialog.update(50)

            sPattern = '''<div id="player_code">.*?<script type='text/javascript'>(eval.+?)</script>'''
            r = re.search(sPattern, html, re.DOTALL + re.IGNORECASE)

            if r:
                sJavascript = r.group(1)
                sUnpacked = jsunpack.unpack(sJavascript)
                sPattern = r"'file\\',\\'(.+?)\\'"
                r = re.search(sPattern, sUnpacked)
                if r:
                    link = r.group(1)
                    dialog.close()
                    return link
            return self.unresolvable()

        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            return self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** sharerepo Error occured: %s' % e)
            self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return 'http://sharerepo.com/%s' % media_id

    def get_host_and_id(self, url):
        r = re.search('//(.+?)/([0-9a-zA-Z]+)', url)
        if r:
            return r.groups()
        return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return (re.match('http://(www.)?sharerepo.com/[\w]+', url) or
                         'sharerepo' in host)
