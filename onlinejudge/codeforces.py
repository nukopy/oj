#!/usr/bin/env python3
import onlinejudge.problem
import onlinejudge.implementation.utils as utils
import onlinejudge.implementation.logging as log
import re
import bs4
import string

# NOTE: Codeforces has its API: http://codeforces.com/api/help
class Codeforces(onlinejudge.problem.OnlineJudge):
    service_name = 'codeforces'

    def __init__(self, contest_id, index, kind=None):
        assert isinstance(contest_id, int)
        assert index in string.ascii_uppercase
        self.contest_id = contest_id
        self.index = index
        self.kind = kind  # It seems 'gym' is specialized, 'contest' and 'problemset' are the same thing
        if kind is None:
            if self.contest_id < 100000:
                self.kind = 'contest'
            else:
                self.kind = 'gym'

    def download(self, session=None):
        url = self.get_url()
        log.status('GET: %s', url)
        resp = session.get(url)
        log.status(utils.describe_status_code(resp.status_code))
        soup = bs4.BeautifulSoup(resp.content, 'lxml')
        samples = utils.SampleZipper()
        for tag in soup.find_all('div', class_=re.compile('^(in|out)put$')):  # Codeforces writes very nice HTML :)
            log.debug('tag: %s', str(tag))
            assert len(list(tag.children))
            title, pre = list(tag.children)
            assert 'title' in title.attrs['class']
            assert pre.name == 'pre'
            s = ''
            for it in pre.children:
                if it.name == 'br':
                    s += '\n'
                else:
                    s += it.string
            samples.add(s, title.string)
        return samples.get()

    def login(self, get_credentials, session=None):
        url = 'http://codeforces.com/enter'
        log.status('GET: %s', url)
        resp = session.get(url)
        log.status(utils.describe_status_code(resp.status_code))
        resp.raise_for_status()
        if resp.url != url:  # redirected
            log.info('You have already signed in.')
            return True
        soup = bs4.BeautifulSoup(resp.content, 'lxml')
        form = soup.find('form', id='enterForm')
        log.debug('form: %s', str(form))
        username, password = get_credentials()
        form = utils.FormSender(form, url=resp.url)
        form.set('handle', username)
        form.set('password', password)
        form.set('remember', 'on')
        resp = form.request(session)
        resp.raise_for_status()
        if resp.url != url:  # redirected
            log.success('Welcome, %s.', username)
            return True
        else:
            log.failure('Invalid handle or password.')
            return False

    def get_url(self):
        table = {}
        table['contest']    = 'http://codeforces.com/contest/{}/problem/{}'
        table['problemset'] = 'http://codeforces.com/problemset/problem/{}/{}'
        table['gym']        = 'http://codeforces.com/gym/{}/problem/{}'
        return table[self.kind].format(self.contest_id, self.index)

    @classmethod
    def from_url(cls, s):
        table = {}
        table['contest']    = r'^http://codeforces\.com/contest/([0-9]+)/problem/([0A-Za-z])/?$'  # e.g. http://codeforces.com/contest/538/problem/H
        table['problemset'] = r'^http://codeforces\.com/problemset/problem/([0-9]+)/([0A-Za-z])/?$'  # e.g. http://codeforces.com/problemset/problem/700/B
        table['gym']        = r'^http://codeforces\.com/gym/([0-9]+)/problem/([0A-Za-z])/?$'  # e.g. http://codeforces.com/gym/101021/problem/A
        normalize = lambda c: c == '0' and 'A' or c.upper()
        for kind, expr in table.items():
            m = re.match(expr, s)
            if m:
                return cls(int(m.group(1)), normalize(m.group(2)), kind=kind)

onlinejudge.problem.list += [ Codeforces ]
