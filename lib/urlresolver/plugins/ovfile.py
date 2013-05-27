"""
ovfile urlresolver plugin
Copyright (C) 2011 anilkuj

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

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
import xbmcgui
#TODO: switch this to the jsunpack lib
from vidxden import unpack_js


class OvfileResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "ovile"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        html = self.net.http_GET(web_url).content

        if 'file has been removed' in html:
            self.unresolvable(1, 'This file has been removed')

        form_values = {}
        for i in re.finditer('<input type="hidden" name="(.+?)" value="(.+?)">', html):
            form_values[i.group(1)] = i.group(2)

        html = self.net.http_POST(web_url, form_data=form_values).content

        page = ''.join(html.splitlines()).replace('\t', '')
        r = re.compile("return p\}\(\'(.+?)\',\d+,\d+,\'(.+?)\'").findall(page)
        if r:
            p = r[1][0]
            k = r[1][1]
        else:
            msg = '%s: packed javascript embed code not found' % self.name
            common.addon.log_error(msg)
            return self.unresolvable(0, msg)
        decrypted_data = unpack_js(p, k)
        r = re.search('file.\',.\'(.+?).\'', decrypted_data)
        if not r:
            r = re.search('src="(.+?)"', decrypted_data)
        if r:
            return r.group(1)
        else:
            msg = '%s: stream url not found' % self.name
            common.addon.log_error(msg)
            return self.unresolvable(0, msg)

    def get_url(self, host, media_id):
        return 'http://www.ovfile.com/%s' % media_id

    def get_host_and_id(self, url):
        r = re.search('http://(.+?)/embed-([\w]+)-', url)
        if r:
            return r.groups()
        else:
            r = re.search('//(.+?)/([\w]+)', url)
            if r:
                return r.groups()
            else:
                return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return (re.match('http://(www.)?ovfile.com/[\w]+', url) or
                'ovfile' in host)
