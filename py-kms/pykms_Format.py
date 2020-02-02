#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
import re
import sys
import os
from collections import OrderedDict

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
            return strg.encode(typ)
    else:
            return strg

def deco(strg, typ = 'latin-1'):
    if pyver >= (3, 0):
        if isinstance(strg, bytes):
            return strg.decode(typ)
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
ColorMapReversed = dict(zip(ColorMap.values(), ColorMap.keys()))
ExtraMapReversed = dict(zip(ExtraMap.values(), ExtraMap.keys()))

MsgMap = {0  : {'text' : "{yellow}\n\t\t\tClient generating RPC Bind Request...{end}",                               'align' : ()},
          1  : {'text' : "{white}<==============={end}{yellow}\tClient sending RPC Bind Request...{end}",            'align' : ()},
          2  : {'text' : "{yellow}Server received RPC Bind Request !!!\t\t\t\t{end}{white}<==============={end}",    'align' : ()},
          3  : {'text' : "{yellow}Server parsing RPC Bind Request...{end}",                                          'align' : ()},
          4  : {'text' : "{yellow}Server generating RPC Bind Response...{end}",                                      'align' : ()},
          5  : {'text' : "{yellow}Server sending RPC Bind Response...\t\t\t\t{end}{white}===============>{end}",     'align' : ()},
          6  : {'text' : "{green}{bold}\nRPC Bind acknowledged !!!{end}",                                            'align' : ()},
          7  : {'text' : "{white}===============>{end}{yellow}\tClient received RPC Bind Response !!!{end}",         'align' : ()},
          8  : {'text' : "{green}{bold}\t\t\tRPC Bind acknowledged !!!{end}",                                        'align' : ()},
          9  : {'text' : "{blue}\t\t\tClient generating Activation Request dictionary...{end}",                      'align' : ()},
          10 : {'text' : "{blue}\t\t\tClient generating Activation Request data...{end}",                            'align' : ()},
          11 : {'text' : "{blue}\t\t\tClient generating RPC Activation Request...{end}",                             'align' : ()},
          12 : {'text' : "{white}<==============={end}{blue}\tClient sending RPC Activation Request...{end}",        'align' : ()},
          13 : {'text' : "{blue}Server received RPC Activation Request !!!\t\t\t{end}{white}<==============={end}",  'align' : ()},
          14 : {'text' : "{blue}Server parsing RPC Activation Request...{end}",                                      'align' : ()},
          15 : {'text' : "{blue}Server processing KMS Activation Request...{end}",                                   'align' : ()},
          16 : {'text' : "{blue}Server processing KMS Activation Response...{end}",                                  'align' : ()},
          17 : {'text' : "{blue}Server generating RPC Activation Response...{end}",                                  'align' : ()},
          18 : {'text' : "{blue}Server sending RPC Activation Response...\t\t\t{end}{white}===============>{end}",   'align' : ()},
          19 : {'text' : "{green}{bold}\nServer responded, now in Stand by...\n{end}",                               'align' : ()},
          20 : {'text' : "{white}===============>{end}{blue}\tClient received Response !!!{end}",                    'align' : ()},
          21 : {'text' : "{green}{bold}\t\t\tActivation Done !!!{end}",                                              'align' : ()},
          -1 : {'text' : "{white}Server receiving{end}",                                                             'align' : ()},
          -2 : {'text' : "{white}\t\t\t\t\t\t\t\tClient sending{end}",                                               'align' : ()},
          -3 : {'text' : "{white}\t\t\t\t\t\t\t\tClient receiving{end}",                                             'align' : ()},
          -4 : {'text' : "{white}Server sending{end}",                                                               'align' : ()},
          }

def unformat_message(symbolic_string_list):
        """ `symbolic_string_list` : a list of strings with symbolic formattation, example:
                                     symbolic_string_list = ["{yellow}\tPluto\n{end}",
                                                             "{reverse}{blue}======>{end}{red}\t\tPaperino{end}"]
            >>> unformat_message(symbolic_string_list)
            >>> [['\tPluto\n'], ['======>', '\t\tPaperino']]
        """
        pattern = r"(?<!\{)\{([^}]+)\}(?!\})"
        picktxt, pickarrw = [ [] for _ in range(2) ]
                                       
        for item in symbolic_string_list:
                try:
                        # only for py-kms MsgMap.
                        picklist = re.sub(pattern, '*', item['text'])
                except:
                        # generalization.
                        picklist = re.sub(pattern, '*', item)
                picklist = list(filter(None, picklist.split('*')))
                picktxt.append(picklist)
        return picktxt

def unshell_message(ansi_string, count):
    """ `ansi_string` : a string with ansi formattation, example:
                        ansi_string = '\x1b[97mPippo\x1b[0m\n\x1b[94mPluto\t\t\x1b[0m\n\x1b[92m\x1b[1m\nPaperino\n\x1b[0m\n
        `count`       : int progressive increment for tag.
        >>> unshell_message(ansi_string count = 0)
        >>> ({'tag00': {'color': 'white', 'extra': [], 'text': 'Pippo'},
              'tag01': {'color': 'blue', 'extra': [], 'text': 'Pluto\t\t'}
              'tag02': {'color': 'green', 'extra': ['bold'], 'text': '\nPaperino\n'}
             }, 3)
    """
    ansi_find = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    ansi_list = re.findall(ansi_find, ansi_string)
    ansi_indx_start = [ n for n in range(len(ansi_string)) for ansi in list(set(ansi_list)) if ansi_string.find(ansi, n) == n ]
    ansi_indx_stop = [ n + len(value) for n, value in zip(ansi_indx_start, ansi_list)]
    ansi_indx = sorted(list(set(ansi_indx_start + ansi_indx_stop)))

    msgcolored = {}

    for k in range(len(ansi_indx) - 1):
        ansi_value = ansi_string[ansi_indx[k] : ansi_indx[k + 1]]
        if ansi_value not in ['\x1b[0m', '\n']:
            tagname = "tag" + str(count).zfill(2)
            if tagname not in msgcolored:
                msgcolored[tagname] = {'color' : '', 'extra' : [], 'text' : ''}

            if ansi_value in ColorMapReversed.keys():
                msgcolored[tagname]['color'] = ColorMapReversed[ansi_value]
            elif ansi_value in ExtraMapReversed.keys():
                msgcolored[tagname]['extra'].append(ExtraMapReversed[ansi_value])
            else:
                    msgcolored[tagname]['text'] = ansi_value
        else:
                if ansi_value != '\n':
                        count += 1
    # Ordering.
    msgcolored = OrderedDict(sorted(msgcolored.items()))

    return msgcolored, count

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

# based on: https://ryanjoneil.github.io/posts/2014-02-14-capturing-stdout-in-a-python-child-process.html,
# but not using threading/multiprocessing so:
# 1) message visualization order preserved.
# 2) newlines_count function output not wrong.
class ShellMessage(object):
    view = True
    count, remain, numlist = (0, 0, [])

    class Collect(StringIO):
        # Capture string sent to stdout.
        def write(self, s):
            StringIO.write(self, s)

    class Process(object):
        def __init__(self, nshell, get_text = False, put_text = None, where = 'srv'):
            self.nshell = nshell
            self.get_text = get_text
            self.put_text = put_text
            self.where = where
            self.plaintext = []
            self.path = os.path.dirname(os.path.abspath( __file__ )) + '/pykms_newlines.txt'
            self.print_queue = Queue.Queue()

        def formatter(self, msgtofrmt):
            if self.newlines:
                text = unformat_message([msgtofrmt])[0][0]
                msgtofrmt = msgtofrmt['text'].replace(text, self.newlines * '\n' + text)
                self.newlines = 0
            else:
                try:
                    # comes from MsgMap.
                    msgtofrmt = msgtofrmt['text']
                except:
                    # comes from `put_text` option.
                    pass
            self.msgfrmt = msgtofrmt.format(**ColorExtraMap)
            if self.get_text:
                self.plaintext.append(unshell_message(self.msgfrmt, count = 0)[0]["tag00"]['text'])

        def newlines_file(self, mode, *args):
            try:
                with open(self.path, mode) as file:
                    if mode in ['w', 'a']:
                        file.write(args[0])
                    elif mode == 'r':
                        data = [int(i) for i in [line.rstrip('\n') for line in file.readlines()]]
                        self.newlines, ShellMessage.remain = data[0], sum(data[1:])
            except:
                with open(self.path, 'w') as file:
                        pass

        def newlines_count(self, num):
            ShellMessage.count += MsgMap[num]['text'].count('\n')
            if num >= 0:
                ShellMessage.numlist.append(num)
                if self.continuecount:
                    # Note: is bypassed '\n' counted after message with arrow,
                    # so isn't: str(len(ShellMessage.numlist) + ShellMessage.count)
                    towrite = str(len(ShellMessage.numlist)) + '\n'
                    self.newlines_file('a', towrite)
                    ShellMessage.count, ShellMessage.numlist = (0, [])
            else:
                ShellMessage.count += (len(ShellMessage.numlist) - ShellMessage.remain) * 2
                if num in [-1, -3]:
                    towrite = str(ShellMessage.count) + '\n'
                    self.newlines_file('w', towrite)
                    ShellMessage.count, ShellMessage.remain, ShellMessage.numlist = (0, 0, [])
                    self.continuecount = True
                elif num in [-2 ,-4]:
                    self.newlines_file('r')
            if num == 21:
                ShellMessage.count, ShellMessage.remain, ShellMessage.numlist = (0, 0, [])
                os.remove(self.path)

        def run(self):
            # view = False part.
            if not ShellMessage.view:
                if self.get_text:
                    self.newlines = 0
                    if self.put_text is not None:
                        for msg in self.put_text:
                            self.formatter(msg)
                    else:
                        for num in self.nshell:
                            self.formatter(MsgMap[num])
                    return self.plaintext
                else:
                    return
            # Do job.
            self.produce()
            toprint = self.consume(timeout = 0.1)
            # Redirect output.
            if sys.stdout.isatty():
                print(toprint)
            else:
                try:
                    # Import after variables creation.
                    from pykms_GuiBase import gui_redirect
                    gui_redirect(toprint, self.where)
                except:
                    print(toprint)
            # Get string/s printed.
            if self.get_text:
                return self.plaintext

        def produce(self):
            # Save everything that would otherwise go to stdout.
            outstream = ShellMessage.Collect()
            sys.stdout = outstream
            
            try:
                self.continuecount = False
                self.newlines = 0

                # Print something.
                if self.put_text is not None:
                    for msg in self.put_text:
                        ShellMessage.count += msg.count('\n')
                        # Append a dummy element.
                        ShellMessage.numlist.append('put')
                        self.formatter(msg)
                        print(self.msgfrmt, end = '\n', flush = True)
                else:
                    for num in self.nshell:
                        self.newlines_count(num)
                        self.formatter(MsgMap[num])
                        print(self.msgfrmt, end = '\n', flush = True)
            except Exception as e:
                print(e, end = '\n', flush = True)
            finally:
                # Restore stdout and send content.
                sys.stdout = sys.__stdout__
                try:
                    self.print_queue.put(outstream.getvalue())
                except Queue.Full:
                    pass

        def consume(self, timeout = None):
            try:
                toprint = self.print_queue.get(block = timeout is not None, timeout = timeout)
                self.print_queue.task_done()
                return toprint
            except Queue.Empty:
                return None

def pretty_printer(**kwargs):
        """kwargs:
                    `log_obj`  --> if logging object specified the text not ansi
                                   formatted is logged.
                    `get_text` --> if True obtain text not ansi formatted,
                                   after printing it with ansi formattation.
                    `put_text` --> a string or list of strings with ansi formattation.
                                   if None refer to `num_text` for printing process.
                    `num_text` --> a number or list of numbers refering numbered message map.
                                   if None `put_text` must be defined for printing process.
                    `to_exit ` --> if True system exit is called.
                    `where`    --> specifies if message is server-side or client-side
                                   (useful for GUI redirect).
        """
        # Set defaults for not defined options.
        options = {'log_obj'  : None,
                   'get_text' : False,
                   'put_text' : None,
                   'num_text' : None,
                   'to_exit'  : False,
                   'where'    : 'srv'
                   }
        options.update(kwargs)
        # Check options.
        if (options['num_text'] is None) and (options['put_text'] is None):
                raise ValueError('One of `num_text` and `put_text` must be provided.')
        elif (options['num_text'] is not None) and (options['put_text'] is not None):
                raise ValueError('These parameters are mutually exclusive.')

        if (options['num_text'] is not None) and (not isinstance(options['num_text'], list)):
                options['num_text'] = [options['num_text']]
        if (options['put_text'] is not None) and (not isinstance(options['put_text'], list)):
                options['put_text'] = [options['put_text']]

        # Overwrite `get_text` (used as hidden).
        if options['put_text']:
                options['get_text'] = True
        elif options['num_text']:
                options['get_text'] = False

        # Process messages.
        plain_messages = ShellMessage.Process(options['num_text'],
                                              get_text = options['get_text'],
                                              put_text = options['put_text'],
                                              where = options['where']).run()

        if options['log_obj']:
                for plain_message in plain_messages:
                        options['log_obj'](plain_message)
        if options['to_exit']:
                sys.exit(1)
