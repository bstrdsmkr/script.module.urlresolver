"""
TheFile.me urlresolver plugin
Copyright (C) 2013 voinage

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

import urllib2
import os
import re

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common

from lib import jsunpack


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class TheFileResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "thefile"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        try:
            html = self.net.http_GET(web_url).content
            r = re.search("<script type='text/javascript'>(.+?)</script>", html, re.DOTALL)
            if r:
                js = jsunpack.unpack(r.group(1))
                r = re.search("'file','(.+?)'", js)
                if r:
                    return r.group(1)
            return self.unresolvable()
        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            return self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** Thefile Error occured: %s' % e)
            return self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return 'http://thefile.me/%s' % media_id

    def get_host_and_id(self, url):
        r = re.match(r'http://(thefile).me/([0-9a-zA-Z]+)', url)
        if r:
            return r.groups()
        return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match(r'http://(thefile).me/([0-9a-zA-Z]+)', url) or 'thefile' in host


