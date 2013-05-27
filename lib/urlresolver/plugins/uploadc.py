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
import re
import os

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class UploadcResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "uploadc"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()
        # modified by mscreations. uploadc now needs the filename after the media id so make sure we match that
        self.pattern = 'http://((?:www.)?uploadc.com)/([0-9a-zA-Z]+/[0-9a-zA-Z/._]+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)

        #get html
        try:
            html = self.net.http_GET(web_url).content

            #send all form values
            sPattern = '<input.*?name="([^"]+)".*?value=([^>]+)>'
            r = re.findall(sPattern, html)
            data = {}
            if r:
                for match in r:
                    name = match[0]
                    value = match[1].replace('"', '')
                    data[name] = value

                html = self.net.http_POST(web_url, data).content
            else:
                return self.unresolvable()

            # modified by mscreations. get the file url from the returned javascript
            match = re.search("addVariable[(]'file','(.+?)'[)]", html, re.DOTALL + re.IGNORECASE)
            if match:
                return match.group(1)

            return self.unresolvable()
        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            return self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** Uploadc Error occured: %s' % e)
            return self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return 'http://www.uploadc.com/%s' % media_id

    def get_host_and_id(self, url):
        r = re.search(self.pattern, url)
        if r:
            return r.groups()
        return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match(self.pattern, url) or self.name in host
