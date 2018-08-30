#! /usr/bin/env python3
import os
import sys
import shutil
import time
import urllib.request, urllib.parse
import http
import http.cookiejar
import json
from datetime import datetime, timedelta
from zipfile import ZipFile, ZIP_STORED
from subprocess import Popen, PIPE

class Option:
    def __init__(self):
        p = os.path.dirname(__file__).replace('\\', '/') + '/'
        self.crdir = '' if p == '/' else p
        self.cmdc = {}
        self.cmdi = {}
        self.op = ''
        self.cls = ''
        self.browser = ''
        self.getch = None
        self.win = False
        self.unix = False
        self.submitlang = []
        sp = ';'
        if len(sys.argv) > 1 : self.op = sys.argv[1].replace('\\', '/')
        if 'win' in sys.platform and 'darwin' != sys.platform:
            self.cls = 'cls'
            self.getch = self.getch_win
            self.win = True
        else:
            self.cls = 'clear'
            self.getch = self.getch_unix
            self.unix = True
            sp = ':'
        with open(self.crdir + 'setting.ini', encoding='UTF-8') as f:
            mode = ''
            for i in f.readlines():
                s = i.strip()
                if len(i) > 1 and i[:2] != '//':
                    if s[0] == '[':
                        mode = s
                    else:
                        s = s.replace('\\', '/')
                        if mode == '[path]':
                            os.environ['PATH'] = os.environ['PATH'] + sp + s
                        if mode == '[browser]':
                            self.browser = s
                        if mode == '[tle]':
                            self.timeout = int(s)
                        if mode == '[compile]':
                            lang, cmd = map(lambda x : x.strip(), s.split(':', 1))
                            self.cmdc[lang] = cmd.split()
                        if mode == '[interpreter]':
                            lang, cmd = map(lambda x : x.strip(), s.split(':', 1))
                            self.cmdi[lang] = cmd.split()
                        if mode == '[submit]':
                            self.submitlang += s.split()
        self.browser_text = '   problempage:[P]' if self.browser else ''
    def getch_unix(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch
    def getch_win(self):
        import msvcrt
        try:
            return msvcrt.getch().decode('utf8')
        except:
            return ''
    def is_unix(self) : return self.unix
    def is_win(self) : return self.win

class AtCoderSubmit:
    def __init__(self, op, url, contest_name):
        self.op = op
        self.username = ''
        self.password = ''
        self.contest_url = url
        self.contest_name = contest_name
        cj = http.cookiejar.LWPCookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        self._login()
    def _login(self):
        with open(self.op.crdir + 'login.txt', encoding='UTF-8') as f:
            for i in f.readlines():
                if 'username' in i:
                    self.username = i.split()[1].strip()
                elif 'password' in i:
                    self.password = i.split()[1].strip()
        user = {'name': self.username, 'password': self.password}
        post = urllib.parse.urlencode(user).encode('utf-8')
        url = 'https://practice.contest.atcoder.jp/login'
        self.opener.open(url, post)
    
    
    

class PAtCoderSubmit:
    def __init__(self):
        self.op = Option()
        
        s = ''
        if self.op.op:
            s = self.op.op
        else:
            s = input('SubmitCodePath = ')
        
        self.path = s.replace('\"', '').replace('\'', '').lstrip().rstrip()
        
        if self._check_file():
            self.contest_name = self._path_to_contest_name(self.path)
            self.url = 'https://' + self.contest_name + '.contest.atcoder.jp'
            print('https://' + self.contest_name + '.contest.atcoder.jp')
            p = ord(self._path_to_problem(self.path))-97
            
            self._fetch_id_session()
            if p < len(self.taskids):
                self.taskid = self.taskids[p]
                l = self.languageids[self.taskid]
                for i in range(len(l)) : print('%3d'%i, l[i][0])
                print('ext', self._file_ext())
                print('problem', self._path_to_problem(self.path).upper())
                self.selectlang = int(input('SelectLanguageNum = '))
                c = input('ext[' + self._file_ext() + '] : ' + l[self.selectlang][0] + ' : yes/no? ').lower()
                if c == 'yes':
                    self.lang = l[self.selectlang][1]
                    self._submit()
                else:
                    print('Cancel')
        else:
            print('file not found')
    def _submit(self):
        data = {}
        data['__session'] = self.session
        data['task_id'] = self.taskid
        data['source_code'] = self._file_to_str()
        data['language_id_' + self.taskid] = self.lang
        data = urllib.parse.urlencode(data).encode('utf-8')
        self.opener.open(self.url + '/submit', data)
        print('Submit')
    def _file_to_str(self):
        path = os.path.abspath(self.path)
        s = ''
        with open(path, 'r') as f : s = f.read()
        f = True
        while f:
            t = s.replace('\n'*3, '\n'*2).replace('\r\n'*3, '\n'*2)
            f = len(s) != len(t)
            s = t
        return s
    def _file_ext(self):
        return self.path.split('.')[-1]
    def _check_file(self):
        return os.path.exists(os.path.abspath(self.path))
    def _path_to_problem(self, path):
        return os.path.abspath(path).replace('\\', '/').split('/')[-1].split('.')[0]
    def _path_to_contest_name(self, path):
        return os.path.abspath(path).replace('\\', '/').split('/')[-2:-1][0]
    def _login(self):
        cj = http.cookiejar.LWPCookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        with open(self.op.crdir + 'login.txt', encoding='UTF-8') as f:
            for i in f.readlines():
                if 'username' in i:
                    self.username = i.split()[1].strip()
                elif 'password' in i:
                    self.password = i.split()[1].strip()
        user = {'name': self.username, 'password': self.password}
        post = urllib.parse.urlencode(user).encode('utf-8')
        url = 'https://practice.contest.atcoder.jp/login'
        self.opener.open(url, post)
    def _fetch_submit_html(self):
        res = self.opener.open(self.url + '/submit')
        self.html = str(res.read().decode('utf-8'))
    def _fetch_id_session(self):
        self._login()
        self._fetch_submit_html()
        self.taskids = []
        self.languageids = {}
        self.session = ''
        for i in self.html.split('\n'):
            if 'language_id_' in i:
                self.taskids += [i.split('language_id_')[1].split('"')[0]]
        for i in self.taskids:
            langs = []
            for j in self.html.split('submit-language-selector-' + i)[1].split('</select>')[0].split('\n'):
                if '<option value="' in j:
                    j = j.strip()
                    j = j.replace('<option value="', '').replace('</option>', '')
                    value, lang = j.split('">')
                    if self._find_lang(lang):
                        langs += [(lang, value)]
            self.languageids[i] = langs[:]
        for i in self.html.split('\n'):
            sp = 'name="__session" value="'
            if sp in i:
                self.session = i.split(sp)[1].split('"')[0]
                break
    def _find_lang(self, lang):
        if not self.op.submitlang : return True
        lang = lang.lower()
        for i in self.op.submitlang:
            if i in lang : return True
        return False
        
        
    
def strlim(s, n):
    if n <= 3:
        s = s[:n]
    elif len(s) > n:
        s = s[:n-3] + '...'
    return s.ljust(n, ' ')

if __name__ == '__main__':
    PAtCoderSubmit()