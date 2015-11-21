import re
import os

from lxml import etree
import requests


COOKIE = '~/.edux.cookie'
EDUX = 'https://edux.fit.cvut.cz/'
COURSES = 'courses/'
CLASSIFICATION = '/classification/view/'
EDIT = '?do=edit'


class EduxIO:

    '''Class providing the interface for reading and writing Edux classification'''

    def __init__(self, *, cookie_file=None, cookie_dict=None):
        if cookie_file and cookie_dict:
            raise ValueError('cookie_file and cookie_dict cannot be used at teh same time')
        if cookie_dict is not None:
            self.cookies = cookie_dict
        else:
            cookie_file = cookie_file or COOKIE
            try:
                self.cookies = self._cookie_from_file(cookie_file)
            except Exception as e:
                raise ValueError('File {} probably does not contain a '
                                 'cookie in name=value syntax'.format(cookie_file)) from e

    @classmethod
    def _cookie_from_file(cls, path):
        with open(os.path.expanduser(path)) as f:
            lines = f.readlines()
        cookies = {}
        for line in lines:
            parts = line.split('=')
            cookies[parts[0]] = parts[1].rstrip()
        return cookies

    def get(self, url):
        r = requests.get(url, cookies=self.cookies)
        self.cookies = r.cookies.get_dict()

        # Hear about return codes, Edux?
        if ('id="nepovolena_akce"' in r.text or
                'id="permission_denied"' in r.text):
            raise ValueError('Your cookie does not work on requested page, permission denied')

        if ('id="stranka_s_timto_nazvem_jeste_neexistuje"' in r.text or
                'id="this_topic_does_not_exist_yet"' in r.text):
            raise ValueError('Requested URL does not exist')

        return r

    def post(self, url, data):
        return requests.post(url, data, cookies=self.cookies)

    def parse_courses_list(self):
        r = requests.get(EDUX)  # do not use our get method, simply grab it without cookies
        return tuple(x[len(COURSES):] for x in set(re.findall(COURSES + r'[^<"]*', r.text))
                     if not x.endswith('KOD-PREDMETU'))

    def parse_classification_tree(self, course=None):
        '''
        Parse all classification types for our course

        If course is not provided, tries to use self.course
        If course is provided and self.course was not set, it sets it
        If course is provided and self.course was set, it uses course and preserves self.course
        If neither course or self.course is provided/set, it blows up

        Returns a weird dict-based tree where leaves contains empty dicts
        '''
        if hasattr(self, 'course'):
            course = course or self.course
        elif course is None:
            raise AttributeError('Neither course attribute or course argument was provided')
        else:
            self.course = course

        classification = EDUX + COURSES + course + CLASSIFICATION
        r = self.get(classification + 'start')
        strings = tuple(x[len(classification):] for x in
                        set(re.findall(classification + r'[^ <"\?#]*', r.text))
                        if not x.startswith(classification + 'start') and not x.endswith('start'))

        tree = {}
        for string in strings:
            walk = tree
            for part in string.split('/'):
                if part not in walk:
                    walk[part] = {}
                walk = walk[part]
        return tree

    def parse_form_edit_score(self, url):
        r = self.get(url)
        tree = etree.HTML(r.text)
        scores_form = None
        for form in tree.findall('.//form'):
            if form.attrib.get('id') in ['cs_form_edit_score', 'en_form_edit_score']:
                scores_form = form
                break
        if scores_form is None:
            raise ValueError('Could not find scores form on parsed page')

        values = {}
        for inp in form.findall('.//input'):
            values[inp.attrib.get('name')] = inp.attrib.get('value', '')
        values.pop(None, None)  # Remove bogus value, such as 'nastavit svislý posun'
        return values

    def submit_form_edit_score(self, data, url):
        return self.post(url, data)
