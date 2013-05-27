"""
dailymotion urlresolver plugin
Copyright (C) 2011 cyrus007

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
import urllib2
import urllib

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common


class DailymotionResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "dailymotion"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        try:
            link = self.net.http_GET(web_url).content
        except urllib2.URLError, e:
            return self.unresolvable(3, str(e))
        sequence = re.compile('"sequence":"(.+?)"').findall(link)
        newseqeunce = urllib.unquote(sequence[0]).decode('utf8').replace('\\/', '/')
        dm_high = re.compile('"hqURL":"(.+?)"').findall(newseqeunce)

        if len(dm_high) == 0:
            dm_low = re.compile('"sdURL":"(.+?)"').findall(newseqeunce)
            return dm_low[0]
        else:
            return dm_high[0]

    def get_url(self, host, media_id):
        return 'http://www.dailymotion.com/video/%s' % media_id

    def get_host_and_id(self, url):
        r = re.search('//(.+?)/video/([0-9A-Za-z]+)', url)
        if r:
            return r.groups()
        else:
            r = re.search('//(.+?)/swf/([0-9A-Za-z]+)', url)
            if r:
                return r.groups()
            else:
                return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match('http://(www.)?dailymotion.com/(video|swf)/[\w]+', url) or \
               self.name in host
