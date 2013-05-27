"""
urlresolver XBMC Addon
Copyright (C) 2013 t0mm0, JUL1EN094, bstrdsmkr

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

import os
import re
import urllib
import urllib2

from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import SiteAuth
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
import xbmcgui
from t0mm0.common.net import Net


#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')


class RealDebridResolver(Plugin, UrlResolver, SiteAuth, PluginSettings):
    implements = [UrlResolver, SiteAuth, PluginSettings]
    name = "realdebrid"
    profile_path = common.profile_path
    cookie_file = os.path.join(profile_path, '%s.cookies' % name)
    media_url = None

    def __init__(self):
        p = self.get_setting('priority') or 1
        self.priority = int(p)
        self.net = Net()
        self.hosters = None
        try:
            os.makedirs(os.path.dirname(self.cookie_file))
        except OSError:
            pass

    #UrlResolver methods
    def get_media_url(self, host, media_id):
        try:
            url = 'http://real-debrid.com/ajax/deb.php?lang=en&sl=1&link=%s' % media_id.replace(
                '|User-Agent=Mozilla%2F5.0%20(Windows%20NT%206.1%3B%20rv%3A11.0)%20Gecko%2F20100101%20Firefox%2F11.0',
                '')
            source = self.net.http_GET(url).content

            if re.search('Upgrade your account now to generate a link', source):
                return self.unresolvable(2, 'Upgrade your account now to generate a link')
            if source == '<span id="generation-error">Your file is unavailable on the hoster.</span>':
                return self.unresolvable(2, 'Your file is unavailable on the hoster')
            if re.search('This hoster is not included in our free offer', source):
                return self.unresolvable(2, 'This hoster is not included in our free offer')
            if re.search('No server is available for this hoster.', source):
                return self.unresolvable(2, 'No server is available for this hoster.')
            link = re.compile('ok"><a href="(.+?)"').findall(source)
            if len(link) == 0:
                return self.unresolvable(0, 'File Not Found or removed')
            self.media_url = link[0]
            return link[0]
        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            self.unresolvable(3, str(e))
        except Exception, e:
            common.addon.log('**** Real Debrid Error occured: %s' % e)
            self.unresolvable(0, str(e))

    def get_url(self, host, media_id):
        return media_id

    def get_host_and_id(self, url):
        return 'www.real-debrid.com', url

    def get_all_hosters(self):
        if self.hosters is None:
            url = 'http://www.real-debrid.com/api/regex.php?type=all'
            response = self.net.http_GET(url).content.lstrip('/').rstrip('/g')
            delim = '/g,/|/g\|-\|/'
            self.hosters = [re.compile(host) for host in re.split(delim, response)]
            common.addon.log_debug('RealDebrid hosters : %s' % self.hosters)
        return self.hosters

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        common.addon.log_debug('%s: in valid_url %s : %s' % (self.name, url, host))
        self.get_all_hosters()
        for host in self.hosters:
            common.addon.log_debug('RealDebrid checking host : %s' % str(host))
            if re.search(host, url):
                common.addon.log_debug('RealDebrid Match found')
                return True
        return False

    def checkLogin(self):
        url = 'http://real-debrid.com/lib/api/account.php'
        if not os.path.exists(self.cookie_file):
            return True
        self.net.set_cookies(self.cookie_file)
        source = self.net.http_GET(url).content
        common.addon.log_debug(source)
        if re.search('expiration', source):
            common.addon.log_debug('checkLogin returning False')
            return False
        else:
            common.addon.log_debug('checkLogin returning True')
            return True

    #SiteAuth methods
    def login(self):
        if self.checkLogin():
            try:
                common.addon.log_debug('Need to login since session is invalid')
                login_data = urllib.urlencode(
                    {'user': self.get_setting('username'), 'pass': self.get_setting('password')})
                url = 'https://real-debrid.com/ajax/login.php?' + login_data
                source = self.net.http_GET(url).content
                if re.search('OK', source):
                    self.net.save_cookies(self.cookie_file)
                    self.net.set_cookies(self.cookie_file)
                    return True
            except:
                common.addon.log_debug('error with http_GET')
                dialog = xbmcgui.Dialog()
                dialog.ok(' Real-Debrid ', ' Unexpected error, Please try again.', '', '')
            else:
                return False
        else:
            return True

    #PluginSettings methods
    def get_settings_xml(self):
        xml = PluginSettings.get_settings_xml(self)
        xml += '<setting id="RealDebridResolver_login" '
        xml += 'type="bool" label="login" default="false"/>\n'
        xml += '<setting id="RealDebridResolver_username" enable="eq(-1,true)" '
        xml += 'type="text" label="username" default=""/>\n'
        xml += '<setting id="RealDebridResolver_password" enable="eq(-2,true)" '
        xml += 'type="text" label="password" option="hidden" default=""/>\n'
        return xml

    #to indicate if this is a universal resolver
    def isUniversal(self):
        return True
