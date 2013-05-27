"""
180upload urlresolver plugin
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
import urllib2
import os

from t0mm0.common.net import Net
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from urlresolver import common
import xbmcgui
import xbmc


net = Net()

#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDSMKR, ELDORADO
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')
datapath = common.profile_path


class OneeightyuploadResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "180upload"

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        print '180upload: in get_media_url %s %s' % (host, media_id)
        web_url = self.get_url(host, media_id)
        try:
            dialog = xbmcgui.DialogProgress()
            dialog.create('Resolving', 'Resolving 180Upload Link...')
            dialog.update(0)

            puzzle_img = os.path.join(datapath, "180_puzzle.png")

            print '180Upload - Requesting GET URL: %s' % web_url
            html = net.http_GET(web_url).content

            dialog.update(50)

            data = {}
            r = re.findall(r'type="hidden" name="(.+?)" value="(.+?)">', html)

            if r:
                for name, value in r:
                    data[name] = value
            else:
                raise Exception('Unable to resolve 180Upload Link')

            #Check for SolveMedia Captcha image
            solvemedia = re.search('<iframe src="(http://api.solvemedia.com.+?)"', html)

            if solvemedia:
                dialog.close()
                html = net.http_GET(solvemedia.group(1)).content
                hugekey = re.search('id="adcopy_challenge" value="(.+?)">', html).group(1)
                open(puzzle_img, 'wb').write(
                    net.http_GET("http://api.solvemedia.com%s" % re.search('<img src="(.+?)"', html).group(1)).content)
                img = xbmcgui.ControlImage(450, 15, 400, 130, puzzle_img)
                wdlg = xbmcgui.WindowDialog()
                wdlg.addControl(img)
                wdlg.show()

                xbmc.sleep(3000)

                kb = xbmc.Keyboard('', 'Type the letters in the image', False)
                kb.doModal()

                if kb.isConfirmed():
                    userInput = kb.getText()
                    if userInput:
                        solution = kb.getText()
                    elif not userInput:
                        Notify('big', 'No text entered', 'You must enter text in the image to access video', '')
                        return False
                else:
                    return False

                wdlg.close()
                dialog.create('Resolving', 'Resolving 180Upload Link...')
                dialog.update(50)
                if solution:
                    data.update({'adcopy_challenge': hugekey, 'adcopy_response': solution})

            print '180Upload - Requesting POST URL: %s' % web_url
            html = net.http_POST(web_url, data).content
            dialog.update(100)

            link = re.search('<a href="(.+?)" onclick="thanks\(\)">Download now!</a>', html)
            if link:
                print '180Upload Link Found: %s' % link.group(1)
                return link.group(1)
            else:
                raise Exception('Unable to resolve 180Upload Link')

        except urllib2.URLError, e:
            common.addon.log_error(self.name + ': got http error %d fetching %s' %
                                   (e.code, web_url))
            common.addon.show_small_popup('Error', 'Http error: ' + str(e), 5000, error_logo)
            return False
        except Exception, e:
            common.addon.log_error('**** 180upload Error occured: %s' % e)
            common.addon.show_small_popup(title='[B][COLOR white]180UPLOAD[/COLOR][/B]',
                                          msg='[COLOR red]%s[/COLOR]' % e, delay=5000, image=error_logo)
            return False

    def get_url(self, host, media_id):
        print '180upload: in get_url %s %s' % (host, media_id)
        return 'http://www.180upload.com/%s' % media_id

    def get_host_and_id(self, url):
        print '180upload: in get_host_and_id %s' % url

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
        return (re.match('http://(www.)?180upload.com/' +
                         '[0-9A-Za-z]+', url) or
                '180upload' in host)
