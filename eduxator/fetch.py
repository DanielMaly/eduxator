import abc
import requests
import os

COOKIE = '~/.edux.cookie'


class EduxFetcher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get(self, url, use_auth):
        raise NotImplementedError('You should override the get() method in your subclass')

    @abc.abstractmethod
    def post(self, url, data):
        raise NotImplementedError('You should override the post() method in your subclass')


class CookieBasedEduxFetcher(EduxFetcher):
    def __init__(self, *, cookie_file=None, cookie_dict=None):
        if cookie_file and cookie_dict:
            raise ValueError('cookie_file and cookie_dict cannot be used at the same time')
        if cookie_dict is not None:
            self.cookies = cookie_dict
        else:
            cookie_file = cookie_file or COOKIE
            try:
                self.cookies = self.cookie_from_file(cookie_file)
            except Exception as e:
                raise ValueError('File {} probably does not contain a '
                                 'cookie in name=value syntax'.format(cookie_file)) from e

    @classmethod
    def cookie_from_file(cls, path):
        with open(os.path.expanduser(path)) as f:
            lines = f.readlines()
        cookies = {}
        for line in lines:
            parts = line.split('=')
            cookies[parts[0]] = parts[1].rstrip()
        return cookies

    def save_cookie(self, path=COOKIE):
        with open(os.path.expanduser(path), 'w') as f:
            for name in self.cookies:
                f.write(name + '=' + self.cookies[name] + '\n')
                break

    def get(self, url, use_auth=True):

        if use_auth:
            r = requests.get(url, cookies=self.cookies)
            self.cookies.update(r.cookies.get_dict())
        else:
            r = requests.get(url)

        # Hear about return codes, Edux?
        if ('id="nepovolena_akce"' in r.text or
                    'id="permission_denied"' in r.text):
            raise ValueError('Your cookie does not work on requested page, permission denied')

        if ('id="stranka_s_timto_nazvem_jeste_neexistuje"' in r.text or
                    'id="this_topic_does_not_exist_yet"' in r.text):
            raise ValueError('Requested URL does not exist')

    def post(self, url, data):
        return requests.post(url, data, cookies=self.cookies)
