#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
import re
import sys
import threading

try:
    # Python 2.x imports
    from StringIO import StringIO
    import Queue as Queue
except ImportError:
    # Python 3.x imports
    from io import StringIO
    import queue as Queue

pyver = sys.version_info[:2]
#----------------------------------------------------------------------------------------------------------------------------------------------------------

def enco(strg, typ = 'latin-1'):
    if pyver >= (3, 0):
        if isinstance(strg, str):
            strgenc = strg.encode(typ)
            return strgenc
    else:
        return strg

def deco(strg, typ = 'latin-1'):
    if pyver >= (3, 0):
        if isinstance(strg, bytes):
            strgdec = strg.decode(typ)
            return strgdec
    else:
        return strg

            
def byterize(obj):
    
    def do_encode(dictio, key):
        if isinstance(dictio[key], str) and len(dictio[key]) > 0 and key not in ['SecondaryAddr']:
            dictio[key] = dictio[key].encode('latin-1')
        elif hasattr(dictio[key], '__dict__'):
            subdictio = dictio[key].__dict__['fields']
            for subkey in subdictio:
                do_encode(subdictio, subkey)

    if pyver >= (3, 0):
        objdict = obj.__dict__['fields']
        for field in objdict:
            do_encode(objdict, field)
            
    return obj


def justify(astring, indent = 35, break_every = 100):
    str_indent = ('\n' + ' ' * indent)
    splitted = astring.split('\n')
    longests = [(n, s) for n, s in enumerate(splitted) if len(s) >= break_every]

    for longest in longests:
        lines = []
        for i in range(0, len(longest[1]), break_every):
            lines.append(longest[1][i : i + break_every])
        splitted[longest[0]] = str_indent.join(lines)
        
    if len(splitted) > 1:
        justy = str_indent.join(splitted)
    else:
        justy = str_indent + str_indent.join(splitted)
   
    return justy

##----------------------------------------------------------------------------------------------------------------------------------------------------
ColorMap = {'gray'       : '\x1b[90m',
            'red'        : '\x1b[91m',
            'green'      : '\x1b[92m',
            'yellow'     : '\x1b[93m',
            'blue'       : '\x1b[94m',
            'magenta'    : '\x1b[95m',
            'cyan'       : '\x1b[96m',
            'white'      : '\x1b[97m'
            }

ExtraMap = {'end'        : '\x1b[0m',
            'bold'       : '\x1b[1m',
            'dim'        : '\x1b[2m',
            'italic'     : '\x1b[3m',
            'underlined' : '\x1b[4m',
            'blink1'     : '\x1b[5m',
            'blink2'     : '\x1b[6m',
            'reverse'    : '\x1b[7m',
            'hidden'     : '\x1b[8m',
            'strike'     : '\x1b[9m'
            }

ColorExtraMap = dict(ColorMap, **ExtraMap)

MsgMap = {0  : {'text' : "{yellow}\n\t\t\tClient generating RPC Bind Request...{end}",                               'where' : "clt"},
          1  : {'text' : "{white}<==============={end}{yellow}\tClient sending RPC Bind Request...{end}",            'where' : "clt"},
          2  : {'text' : "{yellow}Server received RPC Bind Request !!!\t\t\t\t{end}{white}<==============={end}",    'where' : "srv"},
          3  : {'text' : "{yellow}Server parsing RPC Bind Request...{end}",                                          'where' : "srv"},
          4  : {'text' : "{yellow}Server generating RPC Bind Response...{end}",                                      'where' : "srv"},
          5  : {'text' : "{yellow}Server sending RPC Bind Response...\t\t\t\t{end}{white}===============>{end}",     'where' : "srv"},
          6  : {'text' : "{green}{bold}RPC Bind acknowledged !!!\n\n{end}",                                          'where' : "srv"},
          7  : {'text' : "{white}===============>{end}{yellow}\tClient received RPC Bind Response !!!{end}",         'where' : "clt"},
          8  : {'text' : "{green}{bold}\t\t\tRPC Bind acknowledged !!!\n{end}",                                      'where' : "clt"},
          9  : {'text' : "{blue}\t\t\tClient generating Activation Request dictionary...{end}",                      'where' : "clt"},
          10 : {'text' : "{blue}\t\t\tClient generating Activation Request data...{end}",                            'where' : "clt"},
          11 : {'text' : "{blue}\t\t\tClient generating RPC Activation Request...{end}",                             'where' : "clt"},
          12 : {'text' : "{white}<==============={end}{blue}\tClient sending RPC Activation Request...\n\n{end}",    'where' : "clt"},
          13 : {'text' : "{blue}Server received RPC Activation Request !!!\t\t\t{end}{white}<==============={end}",  'where' : "srv"},
          14 : {'text' : "{blue}Server parsing RPC Activation Request...{end}",                                      'where' : "srv"},
          15 : {'text' : "{blue}Server processing KMS Activation Request...{end}",                                   'where' : "srv"},
          16 : {'text' : "{blue}Server processing KMS Activation Response...{end}",                                  'where' : "srv"},
          17 : {'text' : "{blue}Server generating RPC Activation Response...{end}",                                  'where' : "srv"},
          18 : {'text' : "{blue}Server sending RPC Activation Response...\t\t\t{end}{white}===============>{end}",   'where' : "srv"},
          19 : {'text' : "{green}{bold}Server responded, now in Stand by...\n{end}",                                 'where' : "srv"},
          20 : {'text' : "{white}===============>{end}{blue}\tClient received Response !!!{end}",                    'where' : "clt"},
          21 : {'text' : "{green}{bold}\t\t\tActivation Done !!!{end}",                                              'where' : "clt"},
          -1 : {'text' : "{white}Server receiving{end}",                                                             'where' : "clt"},
          -2 : {'text' : "{white}\n\n\t\t\t\t\t\t\t\tClient sending{end}",                                           'where' : "srv"},
          -3 : {'text' : "{white}\t\t\t\t\t\t\t\tClient receiving{end}",                                             'where' : "srv"},
          -4 : {'text' : "{white}\n\nServer sending{end}",                                                           'where' : "clt"},
          
          40 : {'text' : "{red}{bold}Server connection timed out. Exiting...{end}",                                  'where' : "srv"},
          41 : {'text' : "{red}{bold}HWID '{0}' is invalid. Digit {1} non hexadecimal. Exiting...{end}",             'where' : "srv"},
          42 : {'text' : "{red}{bold}HWID '{0}' is invalid. Hex string is odd length. Exiting...{end}",              'where' : "srv"},
          43 : {'text' : "{red}{bold}HWID '{0}' is invalid. Hex string is too short. Exiting...{end}",               'where' : "srv"},
          44 : {'text' : "{red}{bold}HWID '{0}' is invalid. Hex string is too long. Exiting...{end}",                'where' : "srv"},
          45 : {'text' : "{red}{bold}Port number '{0}' is invalid. Enter between 1 - 65535. Exiting...{end}",        'where' : "srv"},
          46 : {'text' : "{red}{bold}{0}. Exiting...{end}",                                                          'where' : "srv"},
          }

def pick_MsgMap(messagelist):
        pattern = r"(?<!\{)\{([^}]+)\}(?!\})"
        picktxt, pickarrw = [ [] for _ in range(2) ]
                                       
        for messageitem in messagelist:
                picklist = re.sub(pattern, '*', messageitem['text'])
                picklist = list(filter(None, picklist.split('*')))
                picktxt.append(picklist[0])
                try:
                        pickarrw.append(picklist[1])
                except IndexError:
                        pass
        return picktxt, pickarrw

def unshell_MsgMap(arrows):
        unMsgMap = {}
        for key, values in MsgMap.items():
                txt = pick_MsgMap([values])

                if txt[0][0] in arrows:
                        unMsgMap.update({txt[1][0] : values['where']})
                else:
                        unMsgMap.update({txt[0][0] : values['where']})
        return unMsgMap
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------
# https://stackoverflow.com/questions/230751/how-to-flush-output-of-print-function
if pyver < (3, 3):
    old_print = print
    
    def print(*args, **kwargs):
        flush = kwargs.pop('flush', False)
        old_print(*args, **kwargs)
        if flush:
            file = kwargs.get('file', sys.stdout)
            file.flush() if file is not None else sys.stdout.flush()

# https://ryanjoneil.github.io/posts/2014-02-14-capturing-stdout-in-a-python-child-process.html
class ShellMessage(object):
    view = True

    class Collect(StringIO):
        # Capture string sent to stdout.
        def write(self, s):
            StringIO.write(self, s)
            
    class Process(object):
        def __init__(self, nshell, get_text = False, put_text = None):
            self.nshell = nshell
            self.print_queue = Queue.Queue()
            self.get_text = get_text
            self.put_text = put_text
            self.plaintext = []

            if not isinstance(nshell, list):
                self.nshell = [nshell]
            if not isinstance(put_text, list):
                self.put_text = [put_text]

        def formatter(self, num):
            if self.put_text is None:
                self.msg = MsgMap[num]['text'].format(**ColorExtraMap)
            else:
                self.msg = MsgMap[num]['text'].format(*self.put_text, **ColorExtraMap)

            if self.get_text:
                self.plaintext.append(unshell_message(self.msg, m = 0)[0]["tag00"]['text'])

        def run(self):           
            if not ShellMessage.view:
                if self.get_text:
                    for num in self.nshell:
                        self.formatter(num)
                    return self.plaintext
                else:
                    return

            # Start thread process.
            print_thread = threading.Thread(target = self.spawn(), args=(self.print_queue,))
            print_thread.setDaemon(True)
            print_thread.start()
            # Do something with output.
            toprint = self.read(0.1) # 0.1 s to let the shell output the result
            # Redirect output.
            if sys.stdout.isatty():
                print(toprint)
            else:
                try:
                    from pykms_GuiBase import gui_redirect # Import after variables creation.
                    gui_redirect(toprint)
                except:
                    print(toprint)
            # Get string/s printed.
            if self.get_text:
                return self.plaintext
                                
        def spawn(self):
            # Save everything that would otherwise go to stdout.
            outstream = ShellMessage.Collect()
            sys.stdout = outstream
            
            try:
                # Print something.
                for num in self.nshell:
                    self.formatter(num)
                    print(self.msg, flush = True)
            finally:
                # Restore stdout and send content.
                sys.stdout = sys.__stdout__
                try:
                    self.print_queue.put(outstream.getvalue())
                except Queue.Full:
                    pass

        def read(self, timeout = None):
            try:
                toprint = self.print_queue.get(block = timeout is not None, timeout = timeout)
                self.print_queue.task_done()
                return toprint
            except Queue.Empty:
                return None


def unshell_message(ansi_string, m):
    ansi_find = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    ansi_list = re.findall(ansi_find, ansi_string)
    ansi_indx_start = [ n for n in range(len(ansi_string)) for ansi in list(set(ansi_list)) if ansi_string.find(ansi, n) == n ]
    ansi_indx_stop = [ n + len(value) for n, value in zip(ansi_indx_start, ansi_list)]
    ansi_indx = sorted(list(set(ansi_indx_start + ansi_indx_stop)))

    msgcolored = {}
    ColorMapReversed = dict(zip(ColorMap.values(), ColorMap.keys()))
    ExtraMapReversed = dict(zip(ExtraMap.values(), ExtraMap.keys()))

    for k in range(len(ansi_indx) - 1):
        ansi_value = ansi_string[ansi_indx[k] : ansi_indx[k + 1]]
        if ansi_value != '\x1b[0m':
            tagname = "tag" + str(m).zfill(2)
            if tagname not in msgcolored:
                msgcolored[tagname] = {'color' : '', 'extra' : [], 'text' : ''}
                
            if ansi_value in ColorMapReversed.keys():
                msgcolored[tagname]['color'] = ColorMapReversed[ansi_value]
            elif ansi_value in ExtraMapReversed.keys():
                msgcolored[tagname]['extra'].append(ExtraMapReversed[ansi_value])
            else:
                msgcolored[tagname]['text'] = ansi_value
        else:
            m += 1
    # Ordering.
    msgcolored = dict(sorted(msgcolored.items()))
            
    return msgcolored, m
