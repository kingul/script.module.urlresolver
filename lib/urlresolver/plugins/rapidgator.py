"""
Copyright (C) 2017 kodistuff1

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

import json, urllib
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class RapidgatorResolver(UrlResolver):
    name = "Rapidgator"
    domains = ["rapidgator.net","rg.to"]
    pattern = '(?://|\.)(rapidgator\.net|rg\.to)/file/([a-z0-9]+)(?=[/?#]|$)'

    def __init__(self):
        self.net = common.Net()
        self.scheme = 'https'
        self.api_base = '%s://rapidgator.net/api/' % (self.scheme)
        self._session_id = self.get_setting('session_id')

    def api_call(self, method, data, http='GET', login=True):
        loop = 0
        while loop < 2:
            loop += 1

            if login:
                data.update({'sid': self._session_id})

            if http == 'GET':
                content = self.net.http_GET(self.api_base + method + '?' + urllib.encode(data)).content
            elif http == 'HEAD':
                content = self.net.http_HEAD(self.api_base + method + '?' + urllib.encode(data)).content
            elif http == 'POST':
                content = self.net.http_POST(self.api_base + method, urllib.encode(data)).content
            else:
                raise ResolverError(self.name + ' Bad Request')

            try:
                content = json.loads(content)
                status = content['response_status']
                response = content['response']
            except:
                raise ResolverError(self.name + ' Bad Response')

            if status == 200:
                return response

            if login and status in [401,402]: # only actually seen 401, although 402 seems possible
                self.login()
                continue

            if 'response_details' in content and content['response_details']:
                raise ResolverError(self.name + ' ' + str(content['response_details']))
            else:
                raise ResolverError(self.name + ' ' + str(status) + ' Error')

    def login(self):
        if self.get_setting('login') == 'false':
            self._session_id = ''
        elif not (self.get_setting('username') and self.get_setting('password')):
            raise ResolverError(self.name + ' Unauthorized')
        else:
            data = {'username': self.get_setting('username'), 'password': self.get_setting('password')}
            try:
                response = self.api_call('user/login', data, http='POST', login=False)
                self._session_id = response['session_id']
            except:
                self._session_id = ''
        self.set_setting('session_id', self._session_id)
        return True if self._session_id else False

    def get_media_url(self, host, media_id):
        data = {'url': self.get_url(media_id)}
        response = self.api_call('file/download', data)
        if 'delay' in response and response['delay'] and reponse['delay'] != '0':
            raise ResolverError(self.name + ' Payment Required')
        if 'url' not in response:
            raise ResolverError(self.name + ' Bad Response')
        return reponse['url'].replace('\\', '')

    def get_url(self, host, media_id):
        return '%s://rapidgator.net/file/%s' % (self.scheme, media_id)

    @classmethod
    def get_settings_xml(cls):
        xml = super(cls, cls).get_settings_xml(include_login=False)
        xml.append('<setting id="%s_login" type="bool" label="login" default="true"/>' % (cls.__name__))
        xml.append('<setting id="%s_username" enable="eq(-1,true)" type="text" label="Username" default=""/>' % (cls.__name__))
        xml.append('<setting id="%s_password" enable="eq(-2,true)" type="text" label="Password" option="hidden" default=""/>' % (cls.__name__))
        xml.append('<setting id="%s_session_id" visible="false" type="text" default=""/>' % (cls.__name__))
        return xml

