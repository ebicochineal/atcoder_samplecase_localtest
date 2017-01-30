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

class Test():
    def __init__(self, op, path, name, url):
        self.op = op
        self.path = path # test_program_path
        self.name = name # contest_name
        self.problem = os.path.basename(path).split('.')[0]
        self.url = url + Test.read(self.op.crdir + 'samplecase/' + name + '/' + self.problem + '/url.txt').strip()
    def _cmd(self, path):
        lang = os.path.splitext(path)[1][1:]
        path = self._try_compile(lang, path)
        if path != None:
            cmd = []
            if lang in self.op.cmdi:
                cmd = self.op.cmdi[lang]
            else:
                cmd = ['[i]']
            return self._cmdio(cmd, path)
        else:
            return None
    def _cmdio(self, cmd, path):
        r = []
        for i in cmd:
            i = i.replace('[i]', path)
            i = i.replace('[c]', path.split('/')[-1].split('.')[0])
            i = i.replace('[o]', self.op.crdir + 'compile/test.exe')
            i = i.replace('[d]', self.op.crdir + 'compile')
            r += [i]
        return r
    def _try_compile(self, lang, path):
        try:
            if lang in self.op.cmdc:
                print('Compile >>> ' + path)
                cmd = self.op.cmdc[lang]
                os.system(' '.join(self._cmdio(cmd, path)))
                path = self.op.crdir + 'compile/test.exe'
            return path
        except:
            return None
    def _run(self, data_in, data_out):
        green = lambda x : '\033[42;30m' + x + '\033[0m'
        yellow = lambda x : '\033[43;30m' + x + '\033[0m'
        data_in_encode = data_in.encode('utf-8')
        din2k = Test.strlim(data_in, 2000)
        dout2k = Test.strlim(data_out, 2000)
        result = []
        start = time.time()
        p = Popen(self.cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        try:
            outerr = p.communicate(input=data_in_encode, timeout=self.op.timeout)
            etime = '%.3f'%(time.time() - start)
            out = outerr[0].decode('utf-8').replace('\r\n', '\n')
            err = outerr[1].decode('utf-8').replace('\r\n', '\n')
            if Test.jadge(out, data_out):
                result = [green('AC '), etime, din2k, dout2k, out]
            elif err == '':
                result = [yellow('WA '), etime, din2k, dout2k, out]
            else:
                result = [yellow('RE '), '-----', din2k, dout2k, err]
        except:
            p.kill()
            p.wait()
            result = [yellow('TLE'), '-----', din2k, dout2k, '']
        return result
    def test(self):
        cr = self.op.crdir
        tc = 'samplecase/'
        nm = self.name + '/'
        pr = self.problem + '/'
        dpath = cr + tc + nm + pr
        self.result = []
        retry = True
        while retry:
            os.system(self.op.cls)
            self.cmd = self._cmd(self.path)
            if self.cmd != None:
                self.result = []
                print('Run >>> ' + ' '.join(self.cmd))
                test_file_list = [x for x in os.listdir(dpath+'test_in')]
                for i in test_file_list:
                    data_in = Test.read(dpath + 'test_in/' + i)
                    data_out = Test.read(dpath + 'test_out/' + i)
                    r = self._run(data_in, data_out)
                    self.result += [r]
                    print(*(list(r[:2])), i)
                retry = self._ui()
            else:
                print('error')
    def _ui(self):
        m = self.op.browser_text
        print('samplecase view:[ENTER]' + m + '   retry:[R]' + '   quit:[Q]')
        while 1:
            c = self.op.getch()
            if c == '\r':
                return self._view_ior()
            if c == 'q':
                return False
            if c == 'r':
                return True
            if c == 'p' and m:
                Popen([self.op.browser, self.url])
    def _view_ior(self):
        n = 0
        m = self.op.browser_text
        while 1:
            self._draw_ior(n)
            c = self.op.getch()
            if c == "\r":
                n = (n + 1) % len(self.result)
            if c == "q":
                return False
            if c == "r":
                return True
            if c == "p" and m:
                Popen([self.op.browser, self.url])
    def _draw_ior(self, n):
        m = self.op.browser_text
        r = self.result[n]
        tw, th = os.get_terminal_size()
        w = tw // 3 - 1
        h = th - 6
        lin = Test.to_list(r[2], w, h)
        lout = Test.to_list(r[3], w, h)
        lprg = Test.to_list(r[4], w, h)
        os.system(self.op.cls)
        print(r[0], r[1], Test.strlim('sample' + str(n), w))
        print(' '.join([Test.strlim('data_in', w), Test.strlim('data_out', w), Test.strlim('program_out', w)]))
        for y in range(h):
            print('|'.join([lin[y], lout[y], lprg[y]]))
        print('-'*(tw-1))
        print(Test.strlim('next:[ENTER]' + m + '   retry:[R]' + '   quit:[Q]', w*2+2))
    def read(path):
        with open(path, 'r') as f:
            return f.read()
    def to_list(s, w, h):
        mlen = lambda x : sum(2 if ord(y) > 255 else 1 for y in x)
        r = []
        for i in s.split('\n'):
            if mlen(i) > w:
                b = ''
                bw = 0
                for j in i:
                    c = mlen(j)
                    if bw + c > w:
                        r += [b]
                        b = ''
                        bw = 0
                    b += j
                    bw += c
                r += [b]
            else:
                r += [i]
        if len(r) < h : r += [''] * (h-len(r))
        if len(r) > h : r = r[:h]
        for i in range(h):
            r[i] = r[i] + ' ' * (w-mlen(r[i]))
        return r
    def jadge(v1, v2):
        if v1 == v2 : return True
        if v1.strip() == v2.strip() : return True
        sp1 = v1.split('\n')
        sp2 = v2.split('\n')
        if len(sp1) != len(sp2) : return False
        for i in range(len(sp1)):
            s1, s2 = sp1[i], sp2[i]
            if s1 != s2:
                try:
                    if (s1[0] == '+' or s2[0] == '+') and s1[0] != s2[0]:
                        return False
                    if round(float(s1), 3) != round(float(s2), 3):
                        return False
                except:
                    return False
        return True
    def strlim(s, n):
        if n <= 3:
            s = s[:n]
        elif len(s) > n:
            s = s[:n-3] + '...'
        return s.ljust(n, ' ')

class Option:
    def __init__(self):
        p = os.path.dirname(__file__).replace('\\', '/') + '/'
        self.crdir = '' if p == '/' else p
        self.cls = ''
        self.cmdc = {}
        self.cmdi = {}
        self.op = ''
        self.cls = ''
        self.browser = ''
        self.getch = None
        sp = ';'
        if len(sys.argv) > 1 : self.op = sys.argv[1].replace('\\', '/')
        if 'win' in sys.platform and 'darwin' != sys.platform:
            self.cls = 'cls'
            self.getch = self.getch_win
        else:
            self.cls = 'clear'
            self.getch = self.getch_unix
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

class AtCoder:
    def __init__(self, op):
        self.op = op
        self.username = ''
        self.password = ''
        self.contest_url = ''
        self.loginstate = False
        cj = http.cookiejar.LWPCookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def _login(self):
        if not self.loginstate:
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
            self.loginstate = True
            print('Login')
    def set_contest_url(self, name): 
        self.name = name
        print(name)
        self.contest_url = 'https://' + self.name + '.contest.atcoder.jp'
    def _get_contest_url(self):
        self._login()
        url = self.contest_url + '/assignments'
        req = self.opener.open(url)
        problem_url = set([])
        t = '<a class="linkwrapper" href="'
        for i in str(req.read()).split('\\n'):
            if t in i:
                problem_url.add(i.split(t, 1)[1].split('"')[0])
        s = 'abcdefghijklmnopqrstuvwxyz'[:len(problem_url)]
        return zip(s, sorted(problem_url))
    def _get_problem(self, url):
        url = self.contest_url + url
        req = self.opener.open(url)
        r = []
        for i in str(req.read().decode('utf-8')).split('<h3>入力例')[1:]:
            din = i.split('<pre>')[1].split('</pre>')[0]
            dout = i.split('<pre>')[2].split('</pre>')[0]
            r += [(din.strip(), dout.strip())]
        return r
    def try_download(self):
        try:
            tdir = self.op.crdir + 'samplecase' + '/' + self.name + '/'
            try_mkdir(tdir)
            for i, j in self._get_contest_url():
                r = self._get_problem(j)
                try_mkdir(tdir + i)
                try_mkdir(tdir + i + '/' + 'test_in')
                try_mkdir(tdir + i + '/' + 'test_out')
                with open(tdir + i + '/' + 'url.txt', 'wb') as f : f.write(j.encode('utf-8'))
                print(i)
                for k in range(len(r)):
                    filename = 'sample{:0>2}'.format(k) + '.txt'
                    pin = i + '/' + 'test_in' + '/' + filename
                    pout = i + '/' + 'test_out' + '/' + filename
                    fin = tdir + pin
                    fout = tdir + pout
                    with open(fin, 'wb') as f : f.write(r[k][0].encode('utf-8'))
                    with open(fout, 'wb') as f : f.write(r[k][1].encode('utf-8'))
            return True
        except:
            return False

class PAtCoder:
    def __init__(self):
        self.op = Option()
        os.system(self.op.cls)
        try_mkdir(self.op.crdir + 'samplecase')
        try_mkdir(self.op.crdir + 'compile')
        try_mkdir(self.op.crdir + 'temp')
        self._select(input('ContestURL or TestCodePath = '))
    def _select(self, s):
        if 'https://' in s or 'http://' in s:
            self._temp_copy(s)
        else:
            s = s.replace('\"', '').replace('\'', '').lstrip().rstrip()
            self._test_atcoder(s)
    def _temp_copy(self, url):
        dir = self.op.crdir + self._url_to_contest_name(url) + '/'
        if os.path.exists(dir):
            pass
        else:
            try:
                num = int(input('abc:4, arc:4, other:? = '))
                try_mkdir(dir)
                print('Create >>> ' + dir)
                temp = self.op.crdir + 'temp' + '/'
                exts = [os.path.splitext(x)[1] for x in os.listdir(temp)]
                for i in 'abcdefghijklmnopqrstuvwxyz'[0:num]:
                    for j in exts:
                        shutil.copyfile(temp + 'temp' + j, dir + i + j)
                print(', '.join(list('abcdefghijklmnopqrstuvwxyz'[0:num])))
                print('Template Copy')
            except:
                pass
    def _test_atcoder(self, path):
        name = self._path_to_contest_name(path)
        atcoder = AtCoder(self.op)
        atcoder.set_contest_url(name)
        if self._check_sample_case(name):
            print('TestCase Download...')
            if atcoder.try_download():
                print('TestCase Download Completed')
                test = Test(self.op, path, name, atcoder.contest_url)
                test.test()
            else:
                print('TestCase Download Failed')
        else:
            test = Test(self.op, path, name, atcoder.contest_url)
            test.test()
            
    def _url_to_contest_name(self, url):
        return url.split('//')[1].split('.')[0]
    def _path_to_contest_name(self, path):
        return path.replace('\\', '/').split('/')[-2:-1][0]
    def _check_sample_case(self, name):
        return not os.path.exists(self.op.crdir + 'samplecase' + '/' + name)

def try_mkdir(dir):
    try:
        if not os.path.exists(dir) : os.mkdir(dir)
    except:
        pass

mode = PAtCoder()
