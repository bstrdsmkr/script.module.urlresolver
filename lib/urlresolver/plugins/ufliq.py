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

import urllib2
import os
import re

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class UfliqResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "ufliq"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()
        #e.g. http://www.ufliq.com/embed-rw52re7f5aul.html
        self.pattern = 'http://((?:www.)?ufliq.com)/(?:embed-)?([0-9a-zA-Z]+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)

        try:
            resp = self.net.http_GET(web_url)
            html = resp.content
            post_url = resp.get_url()

            form_values = {}
            for i in re.finditer('<input type="hidden" name="(.+?)" value="(.+?)">', html):
                form_values[i.group(1)] = i.group(2)

            html = self.net.http_POST(post_url, form_data=form_values).content

            r = re.search('url: \'(.+?)\', autoPlay: false,onBeforeFinish:', html)
            if r:
                return r.group(1)

            return self.unresolvable()
        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            return self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** ufliq Error occured: %s' % e)
            return self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return 'http://www.ufliq.com/embed-%s.html' % media_id

    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            return r.groups()
        return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match(self.pattern, url) or self.name in host
