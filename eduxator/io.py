import re
import os

from lxml import etree
import requests


EDUX = 'https://edux.fit.cvut.cz/'
COURSES = 'courses/'
CLASSIFICATION = '/classification/view/'
EDIT = '?do=edit'


class EduxIO:

    '''Class providing the interface for reading and writing Edux classification'''

    def __init__(self, fetcher=None):
        self.fetcher = fetcher
        self.classpath = None
        self.course = None

    def fetch(self, url, method='GET', data=None):

        if self.fetcher is None:
            raise ValueError('I have no EduxFetcher to work with. Please set one for me.')
        elif method == 'GET':
            return self.fetcher.get(url)
        else:
            return self.fetcher.post(url, data)

    def parse_courses_list(self):
        '''
        Returns all available courses from Edux
        '''
        r = self.fetch(EDUX)  # do not use our get method, simply grab it without cookies
        return tuple(x[len(COURSES):] for x in set(re.findall(COURSES + r'[^<"]*', r.text))
                     if not x.endswith('KOD-PREDMETU'))

    def course_from_url(self, url):
        '''
        Parses the course name form URL
        This is needed bacuase some sourses, such as BI-3DT.1, only redirects (e.g. to BI-3DT)
        '''
        return url.split('/')[4]  # ['https:', '', 'edux.fit.cvut.cz', 'courses', 'HERE'...

    def parse_classification_tree(self):
        '''
        Parse all classification types for our course

        If self.course is not set, it blows up

        Returns a weird dict-based tree where leaves contains empty dicts
        '''
        self.check_attr('course')

        classification = EDUX + COURSES + self.course + CLASSIFICATION
        r = self.fetch(classification + 'start')
        self.course = self.course_from_url(r.url)
        # link is HTML are without EDUX address
        classification = '/' + COURSES + self.course + CLASSIFICATION
        strings = tuple(x[len(classification):] for x in
                        set(re.findall(classification + r'[^ <"\?#]*', r.text))
                        if not x.startswith(classification + 'start') and not x.endswith('start')
                        and not x.endswith('void'))

        tree = {}
        for string in strings:
            walk = tree
            for part in string.split('/'):
                if part not in walk:
                    walk[part] = {}
                walk = walk[part]
        return tree

    def check_attr(self, attribute):
        if not hasattr(self, attribute):
            raise AttributeError(attribute + ' attribute was not provided, cannot continue')

    def construct_form_url(self, *, edit=False):
        self.check_attr('course')
        self.check_attr('classpath')
        extra = EDIT if edit else ''
        return EDUX + COURSES + self.course + CLASSIFICATION + '/'.join(self.classpath) + extra

    def parse_form_edit_score(self):
        '''
        Parse the classification form

        course and classpath attributes have to be set

        classpath is supposed to be list of strings

        Returns a dict of all current values
        '''
        url = self.construct_form_url(edit=True)
        r = self.fetch(url)
        tree = etree.HTML(r.text)
        scores_form = None
        for form in tree.findall('.//form'):
            if form.attrib.get('id') in ['cs_form_edit_score', 'en_form_edit_score']:
                scores_form = form
                break
        if scores_form is None:
            raise ValueError('Could not find scores form on parsed page')

        values = {}
        for inp in scores_form.findall('.//input'):
            values[inp.attrib.get('name')] = inp.attrib.get('value', '')
        values.pop(None, None)  # Remove bogus value, such as 'nastavit svislý posun'
        return values

    def submit_form_edit_score(self, data):
        url = self.construct_form_url()
        return self.fetch(url, method='POST', data=data)

    @classmethod
    def parse_form_key(cls, key):
        return tuple(x[:-1] for x in key.split('[')[1:])

    @classmethod
    def all_of_index(cls, data, index):
        results = set()
        for key in data.keys():
            triplet = cls.parse_form_key(key)
            if len(triplet) == 3:
                results.add(triplet[index])
        return results

    @classmethod
    def all_usernames(cls, data):
        return cls.all_of_index(data, 0)

    @classmethod
    def all_columns(cls, data):
        return cls.all_of_index(data, 2)
