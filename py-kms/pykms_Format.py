#!/usr/bin/env python3

import re
import sys
import os
from collections import OrderedDict
import logging
from io import StringIO
import queue as Queue
from tempfile import gettempdir

#----------------------------------------------------------------------------------------------------------------------------------------------------------

def enco(strg, typ = 'latin-1'):
    if isinstance(strg, str):
        return strg.encode(typ)

def deco(strg, typ = 'latin-1'):
    if isinstance(strg, bytes):
        return strg.decode(typ)
            
def byterize(obj):
    
    def do_encode(dictio, key):
        if isinstance(dictio[key], str) and len(dictio[key]) > 0 and key not in ['SecondaryAddr']:
            dictio[key] = dictio[key].encode('latin-1')
        elif hasattr(dictio[key], '__dict__'):
            subdictio = dictio[key].__dict__['fields']
            for subkey in subdictio:
                do_encode(subdictio, subkey)

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
ColorMap = {'black'      : '\x1b[90m',
            'red'        : '\x1b[91m',
            'green'      : '\x1b[38;2;0;238;118m', # '\x1b[92m'
            'yellow'     : '\x1b[93m',
            'blue'       : '\x1b[94m',
            'magenta'    : '\x1b[38;2;205;0;205m', # '\x1b[95m'
            'cyan'       : '\x1b[96m',
            'white'      : '\x1b[97m',
            'orange'     : '\x1b[38;2;255;165;0m'
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

MsgMap = {0  : {'text' : "{{yellow}}{}{}Client generating RPC Bind Request...{{end}}"                                  .format('\n', '\t' * 3)},
          1  : {'text' : "{{white}}<==============={{end}}{{yellow}}{}Client sending RPC Bind Request...{{end}}"       .format('\t')},
          2  : {'text' : "{{yellow}}Server received RPC Bind Request !!!{}{{end}}{{white}}<==============={{end}}"     .format('\t' * 4)},
          3  : {'text' : "{{yellow}}Server parsing RPC Bind Request...{{end}}"                                         .format()},
          4  : {'text' : "{{yellow}}Server generating RPC Bind Response...{{end}}"                                     .format()},
          5  : {'text' : "{{yellow}}Server sending RPC Bind Response...{}{{end}}{{white}}===============>{{end}}"      .format('\t' * 4)},
          6  : {'text' : "{{green}}{{bold}}{}RPC Bind acknowledged !!!{{end}}"                                         .format('\n')},
          7  : {'text' : "{{white}}===============>{{end}}{{yellow}}{}Client received RPC Bind Response !!!{{end}}"    .format('\t')},
          8  : {'text' : "{{green}}{{bold}}{}RPC Bind acknowledged !!!{{end}}"                                         .format('\t' * 3)},
          9  : {'text' : "{{blue}}{}Client generating Activation Request dictionary...{{end}}"                         .format('\t' * 3)},
          10 : {'text' : "{{blue}}{}Client generating Activation Request data...{{end}}"                               .format('\t' * 3)},
          11 : {'text' : "{{blue}}{}Client generating RPC Activation Request...{{end}}"                                .format('\t' * 3)},
          12 : {'text' : "{{white}}<==============={{end}}{{blue}}{}Client sending RPC Activation Request...{{end}}"   .format('\t')},
          13 : {'text' : "{{blue}}Server received RPC Activation Request !!!{}{{end}}{{white}}<==============={{end}}" .format('\t' * 3)},
          14 : {'text' : "{{blue}}Server parsing RPC Activation Request...{{end}}"                                     .format()},
          15 : {'text' : "{{blue}}Server processing KMS Activation Request...{{end}}"                                  .format()},
          16 : {'text' : "{{blue}}Server processing KMS Activation Response...{{end}}"                                 .format()},
          17 : {'text' : "{{blue}}Server generating RPC Activation Response...{{end}}"                                 .format()},
          18 : {'text' : "{{blue}}Server sending RPC Activation Response...{}{{end}}{{white}}===============>{{end}}"  .format('\t' * 3)},
          19 : {'text' : "{{green}}{{bold}}{}Server responded, now in Stand by...{}{{end}}"                            .format('\n','\n')},
          20 : {'text' : "{{white}}===============>{{end}}{{blue}}{}Client received Response !!!{{end}}"               .format('\t')},
          21 : {'text' : "{{green}}{{bold}}{}Activation Done !!!{{end}}"                                               .format('\t' * 3)},
          -1 : {'text' : "{{white}}Server receiving{{end}}"                                                            .format()},
          -2 : {'text' : "{{white}}{}Client sending{{end}}"                                                            .format('\t' * 8)},
          -3 : {'text' : "{{white}}{}Client receiving{{end}}"                                                          .format('\t' * 8)},
          -4 : {'text' : "{{white}}Server sending{{end}}"                                                              .format()},
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
# based on: https://ryanjoneil.github.io/posts/2014-02-14-capturing-stdout-in-a-python-child-process.html
queue_print = Queue.Queue()

class ShellMessage(object):
    viewsrv, viewclt = (True for _ in range(2))
    asyncmsgsrv, asyncmsgclt = (False for _ in range(2))
    indx, count, remain, numlist, dummy = (0, 0, 0, [], False)
    loggersrv_pty = logging.getLogger('logsrvpty')
    loggerclt_pty = logging.getLogger('logcltpty')

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
            self.path_nl = os.path.join(gettempdir(), 'pykms_newlines.txt')
            self.path_clean_nl = os.path.join(gettempdir(), 'pykms_clean_newlines.txt')
            self.queue_get = Queue.Queue()

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
                self.plaintext.append(unshell_message(self.msgfrmt, count = 0)[0]["tag00"]['text'].strip())

        def newlines_file(self, mode, *args):
            try:
                with open(self.path_nl, mode) as file:
                    if mode in ['w', 'a']:
                        file.write(args[0])
                    elif mode == 'r':
                        data = [int(i) for i in [line.rstrip('\n') for line in file.readlines()]]
                        self.newlines, ShellMessage.remain = data[0], sum(data[1:])
            except:
                with open(self.path_nl, 'w') as file:
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

            self.newlines_clean(num)

        def newlines_clean(self, num):
            if num == 0:
                with open(self.path_clean_nl, 'w') as file:
                    file.write('clean newlines')
            try:
                with open(self.path_clean_nl, 'r') as file:
                    some = file.read()
                if num == 21:
                    ShellMessage.count, ShellMessage.remain, ShellMessage.numlist, ShellMessage.dummy = (0, 0, [], False)
                    os.remove(self.path_nl)
                    os.remove(self.path_clean_nl)
            except:
                if num == 19:
                    ShellMessage.count, ShellMessage.remain, ShellMessage.numlist, ShellMessage.dummy = (0, 0, [], False)
                    os.remove(self.path_nl)

        def putter(self, aqueue, toput):
            try:
                aqueue.put_nowait(toput)
            except Queue.Full:
                pass

        def execute(self):
            self.manage()
            ShellMessage.indx += 1

        def print_logging_setup(self, logger, async_flag, formatter = logging.Formatter('%(name)s %(message)s')):
            from pykms_GuiBase import gui_redirector
            stream = gui_redirector(StringIO())
            handler = logging.StreamHandler(stream)
            handler.name = 'LogStream'
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)

            if logger.handlers:
                logger.handlers = []

            if async_flag:
                from pykms_Misc import MultiProcessingLogHandler
                logger.addHandler(MultiProcessingLogHandler('Thread-AsyncMsg{0}'.format(handler.name), handler = handler))
            else:
                logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        def print_logging(self, toprint):
            if (self.nshell and ((0 in self.nshell) or (2 in self.nshell and not ShellMessage.viewclt))) or ShellMessage.indx == 0:
                from pykms_GuiBase import gui_redirector_setup, gui_redirector_clear
                gui_redirector_setup()
                gui_redirector_clear()
                self.print_logging_setup(ShellMessage.loggersrv_pty, ShellMessage.asyncmsgsrv)
                self.print_logging_setup(ShellMessage.loggerclt_pty, ShellMessage.asyncmsgclt)

            if self.where == 'srv':
                ShellMessage.loggersrv_pty.info(toprint)
            elif self.where == 'clt':
                ShellMessage.loggerclt_pty.info(toprint)

        def notview(self):
            if self.get_text:
                self.newlines = 0
                if self.put_text is not None:
                    for msg in self.put_text:
                        self.formatter(msg)
                else:
                    for num in self.nshell:
                        self.formatter(MsgMap[num])
                self.putter(self.queue_get, self.plaintext)

        def manage(self):
            if not ShellMessage.viewsrv:
                # viewsrv = False, viewclt = True.
                if ShellMessage.viewclt:
                    if self.where == 'srv':
                        self.notview()
                        return
                else:
                    # viewsrv = False, viewclt = False.
                    self.notview()
                    return
            else:
                # viewsrv = True, viewclt = False.
                if not ShellMessage.viewclt:
                    if self.where == 'clt':
                        self.notview()
                        return
                else:
                    # viewsrv = True, viewclt = True.
                    pass

            # Do job.
            self.produce()
            toprint = self.consume(queue_print, timeout = 0.1)

            if sys.stdout.isatty():
                print(toprint, flush = True)
            else:
                try:
                    self.print_logging(toprint)
                except:
                    print(toprint, flush = True)

            # Get string/s printed.
            if self.get_text:
                self.putter(self.queue_get, self.plaintext)
                return

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
                        if ShellMessage.dummy:
                            ShellMessage.numlist.append('put')
                        self.formatter(msg)
                        print(self.msgfrmt, end = '\n', flush = True)
                else:
                    for num in self.nshell:
                        if num == 0:
                            ShellMessage.dummy = True
                        self.newlines_count(num)
                        self.formatter(MsgMap[num])
                        print(self.msgfrmt, end = '\n', flush = True)
            except Exception as e:
                print(e, end = '\n', flush = True)
            finally:
                # Restore stdout and send content.
                sys.stdout = sys.__stdout__
                self.putter(queue_print, outstream.getvalue())

        def consume(self, aqueue, timeout = None):
            try:
                toprint = aqueue.get(block = timeout is not None, timeout = timeout)
                aqueue.task_done()
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
        shmsg = ShellMessage.Process(options['num_text'],
                                     get_text = options['get_text'],
                                     put_text = options['put_text'],
                                     where = options['where'])

        shmsg.execute()
        plain_messages = shmsg.consume(shmsg.queue_get, timeout = None)
        if options['log_obj']:
                for plain_message in plain_messages:
                        options['log_obj'](plain_message)
        if options['to_exit']:
                sys.exit(1)
