#!/usr/bin/env python3

import sys
import logging
import os
import argparse
from logging.handlers import RotatingFileHandler

from pykms_Format import ColorExtraMap, ShellMessage, pretty_printer

#------------------------------------------------------------------------------------------------------------------------------------------------------------

# https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility
# https://stackoverflow.com/questions/17558552/how-do-i-add-custom-field-to-python-log-format-string
# https://stackoverflow.com/questions/1343227/can-pythons-logging-format-be-modified-depending-on-the-message-log-level
# https://stackoverflow.com/questions/14844970/modifying-logging-message-format-based-on-message-logging-level-in-python3

def add_logging_level(levelName, levelNum, methodName = None):
        """ Adds a new logging level to the `logging` module and the currently configured logging class.
        `levelName` becomes an attribute of the `logging` module with the value `levelNum`.
        `methodName` becomes a convenience method for both `logging` itself and the class returned by `logging.getLoggerClass()`
        (usually just `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is used.

        To avoid accidental clobberings of existing attributes, this method will raise an `AttributeError` if the level name
        is already an attribute of the `logging` module or if the method name is already present .

        Example
        -------
        >>> add_logging_level('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5
        """

        if not methodName:
                methodName = levelName.lower()

        if hasattr(logging, levelName) or hasattr(logging, methodName) or hasattr(logging.getLoggerClass(), methodName):
                return

        def logForLevel(self, message, *args, **kwargs):
                if self.isEnabledFor(levelNum):
                        self._log(levelNum, message, args, **kwargs)
        def logToRoot(message, *args, **kwargs):
                logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, levelName)
        setattr(logging, levelName, levelNum)
        setattr(logging.getLoggerClass(), methodName, logForLevel)
        setattr(logging, methodName, logToRoot)

class LevelFormatter(logging.Formatter):
        dfmt = '%a, %d %b %Y %H:%M:%S'
        default_fmt = logging.Formatter('%(message)s', datefmt = dfmt)

        def __init__(self, formats, color = False):
                """ `formats` is a dict { loglevel : logformat } """
                self.formatters = {}
                for loglevel in formats:
                        if color:
                                frmt = self.colorize(formats, loglevel)
                                formats[loglevel] = frmt.format(**ColorExtraMap)

                        self.formatters[loglevel] = logging.Formatter(formats[loglevel], datefmt = self.dfmt)

        def colorize(self, formats, loglevel):
                if loglevel == logging.MININFO:
                        frmt = '{orange}' + formats[loglevel] + '{end}'
                elif loglevel == logging.CRITICAL:
                        frmt = '{magenta}{bold}' + formats[loglevel] + '{end}'
                elif loglevel == logging.ERROR:
                        frmt = '{red}{bold}' + formats[loglevel] + '{end}'
                elif loglevel == logging.WARNING:
                        frmt = '{yellow}{bold}' + formats[loglevel] + '{end}'
                elif loglevel == logging.INFO:
                        frmt = '{cyan}' + formats[loglevel] + '{end}'
                elif loglevel == logging.DEBUG:
                        frmt = '{green}' + formats[loglevel] + '{end}'
                else:
                        frmt = '{end}' + formats[loglevel] + '{end}'
                return frmt

        def format(self, record):
                formatter = self.formatters.get(record.levelno, self.default_fmt)
                return formatter.format(record)

# based on https://github.com/jruere/multiprocessing-logging (license LGPL-3.0)
from multiprocessing import Queue as MPQueue
import queue as Queue
import threading

class MultiProcessingLogHandler(logging.Handler):
        def __init__(self, name, handler = None):
                super(MultiProcessingLogHandler, self).__init__()
                self.queue = MPQueue(-1)
                if handler is None:
                        handler = logging.StreamHandler()
                self.handler = handler
                self.name = handler.name

                self.setLevel(self.handler.level)
                self.setFormatter(self.handler.formatter)
                self.filters = self.handler.filters

                self.is_closed = False
                self.receive_thread = threading.Thread(target = self.receive, name = name)
                self.receive_thread.daemon = True
                self.receive_thread.start()

        def setFormatter(self, fmt):
                super(MultiProcessingLogHandler, self).setFormatter(fmt)
                self.handler.setFormatter(fmt)

        def emit(self, record):
                try:
                        if record.args:
                                record.msg = record.msg %record.args
                                record.args = None
                        if record.exc_info:
                                dummy = self.format(record)
                                record.exc_info = None
                        self.queue.put_nowait(record)
                except (KeyboardInterrupt, SystemExit):
                        raise
                except:
                        self.handleError(record)

        def receive(self):
                while not (self.is_closed and self.queue.empty()):
                        try:
                                record = self.queue.get(timeout = 0.2)
                                self.handler.emit(record)
                        except (KeyboardInterrupt, SystemExit):
                                raise
                        except EOFError:
                                break
                        except Queue.Empty:
                                pass
                        except:
                                logging.exception('Error in log handler.')
                self.queue.close()
                self.queue.join_thread()

        def close(self):
                if not self.is_closed:
                        self.is_closed = True
                        self.receive_thread.join(5.0)
                        self.handler.close()
                        super(MultiProcessingLogHandler, self).close()


def logger_create(log_obj, config, mode = 'a'):
        # Create new level.
        num_lvl_mininfo = 25
        add_logging_level('MININFO', num_lvl_mininfo)
        log_handlers = []

        # Configure visualization.
        if any(opt in ['STDOUT', 'FILESTDOUT', 'STDOUTOFF'] for opt in config['logfile']):
                if any(opt in ['STDOUT', 'FILESTDOUT'] for opt in config['logfile']):
                        # STDOUT or FILESTDOUT.
                        hand_stdout = logging.StreamHandler(sys.stdout)
                        hand_stdout.name = 'LogStdout'
                        log_handlers.append(hand_stdout)
                if any(opt in ['STDOUTOFF', 'FILESTDOUT'] for opt in config['logfile']):
                        # STDOUTOFF or FILESTDOUT.
                        hand_rotate = RotatingFileHandler(filename = config['logfile'][1], mode = mode, maxBytes = int(config['logsize'] * 1024 * 512),
                                                          backupCount = 1, encoding = None, delay = 0)
                        hand_rotate.name = 'LogRotate'
                        log_handlers.append(hand_rotate)
        elif 'FILEOFF' in config['logfile']:
                hand_null = logging.FileHandler(os.devnull)
                hand_null.name = 'LogNull'
                log_handlers.append(hand_null)
        else:
                # FILE.
                hand_rotate = RotatingFileHandler(filename = config['logfile'][0], mode = mode, maxBytes = int(config['logsize'] * 1024 * 512),
                                                  backupCount = 1, encoding = None, delay = 0)
                hand_rotate.name = 'LogRotate'
                log_handlers.append(hand_rotate)

        # Configure formattation.
        try:
                levelnames = logging._levelToName
        except AttributeError:
                levelnames = logging._levelNames
        levelnum = [k for k in levelnames if k != 0]

        frmt_gen = '%(asctime)s %(levelname)-8s %(message)s'
        frmt_std = '%(asctime)s %(levelname)-8s %(message)s'
        frmt_min = '%(asctime)s %(levelname)-8s %(host)s   %(status)s   %(product)s  %(message)s'
        frmt_name = '%(name)s '

        from pykms_Server import serverthread
        if serverthread.with_gui:
                frmt_std = frmt_name + frmt_std
                frmt_min = frmt_name + frmt_min

        def apply_formatter(levelnum, formats, handler, color = False):
                levelformdict = {}
                for num in levelnum:
                        if num != num_lvl_mininfo:
                                levelformdict[num] = formats[0]
                        else:
                                levelformdict[num] = formats[1]
                handler.setFormatter(LevelFormatter(levelformdict, color = color))
                return handler

        # Clear old handlers.
        if log_obj.handlers:
                log_obj.handlers = []

        for log_handler in log_handlers:
                log_handler.setLevel(config['loglevel'])
                if log_handler.name in ['LogStdout']:
                        log_handler = apply_formatter(levelnum, (frmt_std, frmt_min), log_handler, color = True)
                elif log_handler.name in ['LogRotate']:
                        log_handler = apply_formatter(levelnum, (frmt_gen, frmt_min), log_handler)
                # Attach.
                if config['asyncmsg']:
                        log_obj.addHandler(MultiProcessingLogHandler('Thread-AsyncMsg{0}'.format(log_handler.name), handler = log_handler))
                else:
                        log_obj.addHandler(log_handler)

        log_obj.setLevel(config['loglevel'])

#------------------------------------------------------------------------------------------------------------------------------------------------------------
def check_dir(path, where, log_obj = None, argument = '-F/--logfile'):
        filename = os.path.basename(path)
        pathname = os.path.dirname(path)
        extension = os.path.splitext(filename)[1]

        if pathname == os.sep:
                pathname += filename

        msg_dir  = "{reverse}{red}{bold}argument `%s`: invalid directory: '%s'. Exiting...{end}"
        msg_fil = "{reverse}{red}{bold}argument `%s`: not a %s file, invalid extension: '%s'. Exiting...{end}"

        if not os.path.isdir(pathname):
                if path.count('/') == 0:
                        pathname = filename
                pretty_printer(log_obj = log_obj, where = where, to_exit = True,
                               put_text = msg_dir %(argument, pathname))

def check_logfile(optionlog, defaultlog, where):
        if not isinstance(optionlog, list):
                optionlog = [optionlog]

        lenopt = len(optionlog)
        msg_long = "{reverse}{red}{bold}argument `-F/--logfile`: too much arguments. Exiting...{end}"

        if lenopt > 2:
                pretty_printer(put_text = msg_long, where = where, to_exit = True)

        if (any(opt in ['FILESTDOUT', 'STDOUTOFF'] for opt in optionlog)):
                if lenopt == 1:
                        # add default logfile.
                        optionlog.append(defaultlog)
                elif lenopt == 2:
                        # check directory path.
                        check_dir(optionlog[1], where)
        else:
                if lenopt == 2:
                        pretty_printer(put_text = msg_long, where = where, to_exit = True)
                elif lenopt == 1 and (any(opt not in ['STDOUT', 'FILEOFF'] for opt in optionlog)):
                        # check directory path.
                        check_dir(optionlog[0], where)

        return optionlog

#------------------------------------------------------------------------------------------------------------------------------------------------------------

# Valid language identifiers to be used in the EPID (see "kms.c" in vlmcsd)
ValidLcid = [1025, 1026, 1027, 1028, 1029,
             1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039,
             1040, 1041, 1042, 1043, 1044, 1045, 1046, 1048, 1049,
             1050, 1051, 1052, 1053, 1054, 1056, 1057, 1058, 1059,
             1060, 1061, 1062, 1063, 1065, 1066, 1067, 1068, 1069,
             1071, 1074, 1076, 1077, 1078, 1079,
             1080, 1081, 1082, 1083, 1086, 1087, 1088, 1089,
             1091, 1092, 1093, 1094, 1095, 1097, 1098, 1099,
             1100, 1102, 1103, 1104, 1106, 1110, 1111, 1114, 1125, 1131, 1153,
             2049, 2052, 2055, 2057, 2058, 2060, 2064, 2067, 2068, 2070, 2074, 2077, 2092, 2107, 2110, 2115, 2155,
             3073, 3076, 3079, 3081, 3082, 3084, 3098, 3131, 3179,
             4097, 4100, 4103, 4105, 4106, 4108, 4122, 4155,
             5121, 5124, 5127, 5129, 5130, 5132, 5146, 5179,
             6145, 6153, 6154, 6156, 6170, 6203,
             7169, 7177, 7178, 7194, 7227,
             8193, 8201, 8202, 8251,
             9217, 9225, 9226, 9275,
             10241, 10249, 10250, 11265, 11273, 11274, 12289, 12297, 12298,
             13313, 13321, 13322, 14337, 14346, 15361, 15370, 16385, 16394, 17418, 18442, 19466, 20490]

# http://stackoverflow.com/questions/3425294/how-to-detect-the-os-default-language-in-python
def check_lcid(lcid, log_obj):
        if not lcid or (lcid not in ValidLcid):
                if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython':
                        fixlcid = 1033
                elif os.name == 'nt':
                        import ctypes

                        fixlcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                else:
                        import locale

                        try:
                                fixlcid = next(k for k, v in locale.windows_locale.items() if v == locale.getdefaultlocale()[0])
                        except StopIteration:
                                fixlcid = 1033
                pretty_printer(log_obj = log_obj, put_text = "{reverse}{yellow}{bold}LCID '%s' auto-fixed with LCID '%s'{end}" %(lcid, fixlcid))
                return fixlcid
        return lcid

#------------------------------------------------------------------------------------------------------------------------------------------------------------

class KmsParserException(Exception):
        pass

class KmsParser(argparse.ArgumentParser):
        def error(self, message):
                raise KmsParserException(message)

class KmsParserHelp(object):
        def replace(self, parser, replace_epilog_with):
                text = parser.format_help().splitlines()
                help_list = []
                for line in text:
                        if line == parser.description:
                                continue
                        if line == parser.epilog:
                                line = replace_epilog_with
                        help_list.append(line)
                return help_list

        def printer(self, parsers):
                parser_base = parsers[0]
                if len(parsers) == 1:
                        replace_epilog_with = ''
                else:
                        parser_adj_0, parser_sub_0 = parsers[1]
                        replace_epilog_with = 80 * '*' + '\n'
                        if len(parsers) == 3:
                                parser_adj_1, parser_sub_1 = parsers[2]

                print('\n' + parser_base.description)
                print(len(parser_base.description) * '-' + '\n')
                for line in self.replace(parser_base, replace_epilog_with):
                        print(line)

                def subprinter(adj, sub, replace):
                        print(adj.description + '\n')
                        for line in self.replace(sub, replace):
                                print(line)
                        print('\n')

                if len(parsers) >= 2:
                        subprinter(parser_adj_0, parser_sub_0, replace_epilog_with)
                        if len(parsers) == 3:
                                print(replace_epilog_with)
                                subprinter(parser_adj_1, parser_sub_1, replace_epilog_with)

                print('\n' + len(parser_base.epilog) * '-')
                print(parser_base.epilog + '\n')
                parser_base.exit()

def kms_parser_get(parser):
        zeroarg, onearg = ([] for _ in range(2))
        act = vars(parser)['_actions']
        for i in range(len(act)):
                if act[i].option_strings not in ([], ['-h', '--help']):
                        if isinstance(act[i], argparse._StoreAction) or isinstance(act[i], argparse._AppendAction):
                                onearg.append(act[i].option_strings)
                        else:
                                zeroarg.append(act[i].option_strings)
        return zeroarg, onearg

def kms_parser_check_optionals(userarg, zeroarg, onearg, msg = 'optional py-kms server', exclude_opt_len = [], exclude_opt_dup = []):
        """
        For optionals arguments:
        Don't allow duplicates,
        Don't allow abbreviations,
        Don't allow joining and not existing arguments,
        Checks length values passed to arguments.
        """
        zeroarg = [item for sublist in zeroarg for item in sublist]
        onearg = [item for sublist in onearg for item in sublist]
        allarg = zeroarg + onearg

        def is_abbrev(allarg, arg_to_check):
                extended = []
                for opt in allarg:
                        if len(opt) > 2 and opt[2] == arg_to_check[2]:
                                for indx in range(-1, -len(opt), -1):
                                        if opt[:indx] == arg_to_check:
                                                extended.append(opt)
                return extended

        # Check abbreviations, joining, not existing.
        for arg in userarg:
                if arg not in allarg:
                        if arg.startswith('-'):
                                if arg == '--' or arg[:2] != '--':
                                        raise KmsParserException("unrecognized %s arguments: `%s`" %(msg, arg))
                                else:
                                        extended = is_abbrev(allarg, arg)
                                        if extended:
                                                raise KmsParserException("%s argument `%s` abbreviation not allowed for `%s`" %(msg, arg, ', '.join(extended)))

        # Check duplicates.
        founds = [i for i in userarg if i in allarg]
        dup = [item for item in set(founds) if founds.count(item) > 1]
        for d in dup:
                if d not in exclude_opt_dup:
                        raise KmsParserException("%s argument `%s` appears several times" %(msg, ', '.join(dup)))

        # Check length.
        elem = None
        for found in set(founds):
                if found not in exclude_opt_len:
                        pos = userarg.index(found)
                        try:
                                if found in zeroarg:
                                        elem = userarg[pos + 1]
                                        num = "zero arguments,"
                                elif found in onearg:
                                        elem = userarg[pos + 2]
                                        num = "one argument,"
                        except IndexError:
                                pass

                        if elem and elem not in allarg:
                                raise KmsParserException("%s argument `" %msg + found + "`:" + " expected " + num + " unrecognized: '%s'" %elem)

def kms_parser_check_positionals(config, parse_method, arguments = [], force_parse = False, msg = 'positional py-kms server'):
        try:
                if arguments or force_parse:
                        config.update(vars(parse_method(arguments)))
                else:
                        config.update(vars(parse_method()))
        except KmsParserException as e:
                e = str(e)
                if e.startswith('argument'):
                        raise
                else:
                        raise KmsParserException("unrecognized %s arguments: '%s'" %(msg, e.split(': ')[1]))

def kms_parser_check_connect(config, options, userarg, zeroarg, onearg):
        if 'listen' in config:
                try:
                        lung = len(config['listen'])
                except TypeError:
                        raise KmsParserException("optional connect arguments missing")

                rng = range(lung - 1)
                config['backlog_main'] = options['backlog']['def']
                config['reuse_main'] = options['reuse']['def']

                def assign(arguments, index, options, config, default, islast = False):
                        if all(opt not in arguments for opt in options):
                                if config and islast:
                                        config.append(default)
                                elif config:
                                        config.insert(index, default)
                                else:
                                        config.append(default)

                def assign_main(arguments, config):
                        if any(opt in arguments for opt in ['-b', '--backlog']):
                                config['backlog_main'] = config['backlog'][0]
                                config['backlog'].pop(0)
                        if any(opt in arguments for opt in ['-u', '--no-reuse']):
                                config['reuse_main'] = config['reuse'][0]
                                config['reuse'].pop(0)

                if config['listen']:
                        # check before.
                        pos = userarg.index(config['listen'][0])
                        assign_main(userarg[1 : pos - 1], config)

                        # check middle.
                        for indx in rng:
                                pos1 = userarg.index(config['listen'][indx])
                                pos2 = userarg.index(config['listen'][indx + 1])
                                arguments = userarg[pos1 + 1 : pos2 - 1]
                                kms_parser_check_optionals(arguments, zeroarg, onearg, msg = 'optional connect')
                                assign(arguments, indx, ['-b', '--backlog'], config['backlog'], config['backlog_main'])
                                assign(arguments, indx, ['-u', '--no-reuse'], config['reuse'], config['reuse_main'])

                                if not arguments:
                                        config['backlog'][indx] = config['backlog_main']
                                        config['reuse'][indx] = config['reuse_main']

                        # check after.
                        if lung == 1:
                                indx = -1

                        pos = userarg.index(config['listen'][indx + 1])
                        arguments = userarg[pos + 1:]
                        kms_parser_check_optionals(arguments, zeroarg, onearg, msg = 'optional connect')
                        assign(arguments, None, ['-b', '--backlog'], config['backlog'], config['backlog_main'], islast = True)
                        assign(arguments, None, ['-u', '--no-reuse'], config['reuse'], config['reuse_main'], islast = True)

                        if not arguments:
                                config['backlog'][indx + 1] = config['backlog_main']
                                config['reuse'][indx + 1] = config['reuse_main']
                else:
                        assign_main(userarg[1:], config)


#------------------------------------------------------------------------------------------------------------------------------------------------------------
def proper_none(dictionary):
        for key in dictionary.keys():
                dictionary[key] = None if dictionary[key] == 'None' else dictionary[key]

def check_setup(config, options, logger, where):
        # 'None'--> None.
        proper_none(config)

        # Check logfile.
        config['logfile'] = check_logfile(config['logfile'], options['lfile']['def'], where = where)

        # Check logsize (py-kms Gui).
        if config['logsize'] == "":
                if any(opt in ['STDOUT', 'FILEOFF'] for opt in config['logfile']):
                        # set a recognized size never used.
                        config['logsize'] = 0
                else:
                        pretty_printer(put_text = "{reverse}{red}{bold}argument `-S/--logsize`: invalid with: '%s'. Exiting...{end}" %config['logsize'],
                                       where = where, to_exit = True)

        # Check loglevel (py-kms Gui).
        if config['loglevel'] == "":
                # set a recognized level never used.
                config['loglevel'] = 'ERROR'

        # Setup hidden / asynchronous messages.
        hidden = ['STDOUT', 'FILESTDOUT', 'STDOUTOFF']
        view_flag = (False if any(opt in hidden for opt in config['logfile']) else True)
        if where == 'srv':
                ShellMessage.viewsrv = view_flag
                ShellMessage.asyncmsgsrv = config['asyncmsg']
        elif where == 'clt':
                ShellMessage.viewclt = view_flag
                ShellMessage.asyncmsgclt = config['asyncmsg']

        # Create log.
        logger_create(logger, config, mode = 'a')

        # Check port.
        if (config['port'] == "") or (not 1 <= config['port'] <= 65535):
                pretty_printer(log_obj = logger.error, where = where, to_exit = True,
                               put_text = "{reverse}{red}{bold}Port number '%s' is invalid. Enter between 1 - 65535. Exiting...{end}" %config['port'])

def check_other(config, options, logger, where):
        for dest, stropt in options:
                try:
                        config[dest] = int(config[dest])
                except:
                        if config[dest] is not None:
                                pretty_printer(log_obj = logger.error, where = where, to_exit = True,
                                               put_text = "{reverse}{red}{bold}argument `%s`: invalid with: '%s'. Exiting...{end}" %(stropt, config[dest]))

#------------------------------------------------------------------------------------------------------------------------------------------------------------

# http://joshpoley.blogspot.com/2011/09/hresults-user-0x004.html  (slerror.h)
ErrorCodes = {
        'SL_E_SRV_INVALID_PUBLISH_LICENSE' : (0xC004B001, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_INVALID_PRODUCT_KEY_LICENSE' : (0xC004B002, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_INVALID_RIGHTS_ACCOUNT_LICENSE' : (0xC004B003, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_INVALID_LICENSE_STRUCTURE' : (0xC004B004, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_AUTHORIZATION_FAILED' : (0xC004B005, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_INVALID_BINDING' : (0xC004B006, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_SERVER_PONG' : (0xC004B007, 'The activation server reported that the computer could not connect to the activation server.'),
        'SL_E_SRV_INVALID_PAYLOAD' : (0xC004B008, 'The activation server determined that the product could not be activated.'),
        'SL_E_SRV_INVALID_SECURITY_PROCESSOR_LICENSE' : (0xC004B009, 'The activation server determined that the license is invalid.'),
        'SL_E_SRV_BUSINESS_TOKEN_ENTRY_NOT_FOUND' : (0xC004B010, 'The activation server determined that required business token entry cannot be found.'),
        'SL_E_SRV_CLIENT_CLOCK_OUT_OF_SYNC' : (0xC004B011, 'The activation server determined that your computer clock time is not correct. You must correct your clock before you can activate.'),
        'SL_E_SRV_GENERAL_ERROR' : (0xC004B100, 'The activation server determined that the product could not be activated.'),
        'SL_E_CHPA_PRODUCT_KEY_OUT_OF_RANGE' : (0xC004C001, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_INVALID_BINDING' : (0xC004C002, 'The activation server determined there is a problem with the specified product key.'),
        'SL_E_CHPA_PRODUCT_KEY_BLOCKED' : (0xC004C003, 'The activation server determined the specified product key has been blocked.'),
        'SL_E_CHPA_INVALID_PRODUCT_KEY' : (0xC004C004, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_BINDING_NOT_FOUND' : (0xC004C005, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_BINDING_MAPPING_NOT_FOUND' : (0xC004C006, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_UNSUPPORTED_PRODUCT_KEY' : (0xC004C007, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_MAXIMUM_UNLOCK_EXCEEDED' : (0xC004C008, 'The activation server reported that the product key has exceeded its unlock limit.'),
        'SL_E_CHPA_ACTCONFIG_ID_NOT_FOUND' : (0xC004C009, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_INVALID_PRODUCT_DATA_ID' : (0xC004C00A, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_INVALID_PRODUCT_DATA' : (0xC004C00B, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_SYSTEM_ERROR' : (0xC004C00C, 'The activation server experienced an error.'),
        'SL_E_CHPA_INVALID_ACTCONFIG_ID' : (0xC004C00D, 'The activation server determined the product key is not valid.'),
        'SL_E_CHPA_INVALID_PRODUCT_KEY_LENGTH' : (0xC004C00E, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_INVALID_PRODUCT_KEY_FORMAT' : (0xC004C00F, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_INVALID_PRODUCT_KEY_CHAR' : (0xC004C010, 'The activation server determined the specified product key is invalid.'),
        'SL_E_CHPA_INVALID_BINDING_URI' : (0xC004C011, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_NETWORK_ERROR' : (0xC004C012, 'The activation server experienced a network error.'),
        'SL_E_CHPA_DATABASE_ERROR' : (0xC004C013, 'The activation server experienced an error.'),
        'SL_E_CHPA_INVALID_ARGUMENT' : (0xC004C014, 'The activation server experienced an error.'),
        'SL_E_CHPA_RESPONSE_NOT_AVAILABLE' : (0xC004C015, 'The activation server experienced an error.'),
        'SL_E_CHPA_OEM_SLP_COA0' : (0xC004C016, 'The activation server reported that the specified product key cannot be used for online activation.'),
        'SL_E_CHPA_PRODUCT_KEY_BLOCKED_IPLOCATION' : (0xC004C017, 'The activation server determined the specified product key has been blocked for this geographic location.'),
        'SL_E_CHPA_DMAK_LIMIT_EXCEEDED' : (0xC004C020, 'The activation server reported that the Multiple Activation Key has exceeded its limit.'),
        'SL_E_CHPA_DMAK_EXTENSION_LIMIT_EXCEEDED' : (0xC004C021, 'The activation server reported that the Multiple Activation Key extension limit has been exceeded.'),
        'SL_E_CHPA_REISSUANCE_LIMIT_NOT_FOUND' : (0xC004C022, 'The activation server reported that the re-issuance limit was not found.'),
        'SL_E_CHPA_OVERRIDE_REQUEST_NOT_FOUND' : (0xC004C023, 'The activation server reported that the override request was not found.'),
        'SL_E_CHPA_TIMEBASED_ACTIVATION_BEFORE_START_DATE' : (0xC004C030, 'The activation server reported that time based activation attempted before start date.'),
        'SL_E_CHPA_TIMEBASED_ACTIVATION_AFTER_END_DATE' : (0xC004C031, 'The activation server reported that time based activation attempted after end date.'),
        'SL_E_CHPA_TIMEBASED_ACTIVATION_NOT_AVAILABLE' : (0xC004C032, 'The activation server reported that new time based activation is not available.'),
        'SL_E_CHPA_TIMEBASED_PRODUCT_KEY_NOT_CONFIGURED' : (0xC004C033, 'The activation server reported that the time based product key is not configured for activation.'),
        'SL_E_CHPA_NO_RULES_TO_ACTIVATE' : (0xC004C04F, 'The activation server reported that no business rules available to activate specified product key.'),
        'SL_E_CHPA_GENERAL_ERROR' : (0xC004C050, 'The activation server experienced a general error.'),
        'SL_E_CHPA_DIGITALMARKER_INVALID_BINDING' : (0xC004C051, 'The activation server determined the license is invalid.'),
        'SL_E_CHPA_DIGITALMARKER_BINDING_NOT_CONFIGURED' : (0xC004C052, 'The activation server determined there is a problem with the specified product key.'),
        'SL_E_CHPA_DYNAMICALLY_BLOCKED_PRODUCT_KEY' : (0xC004C060, 'The activation server determined the specified product key has been blocked.'),
        'SL_E_INVALID_LICENSE_STATE_BREACH_GRACE' : (0xC004C291, 'Genuine Validation determined the license state is invalid.'),
        'SL_E_INVALID_LICENSE_STATE_BREACH_GRACE_EXPIRED' : (0xC004C292, 'Genuine Validation determined the license state is invalid.'),
        'SL_E_INVALID_TEMPLATE_ID' : (0xC004C2F6, 'Genuine Validation determined the validation input template identifier is invalid.'),
        'SL_E_INVALID_XML_BLOB' : (0xC004C2FA, 'Genuine Validation determined the validation input data blob is invalid.'),
        'SL_E_VALIDATION_BLOB_PARAM_NOT_FOUND' : (0xC004C327, 'Genuine Validation determined the validation input data blob parameter is invalid.'),
        'SL_E_INVALID_CLIENT_TOKEN' : (0xC004C328, 'Genuine Validation determined the client token data is invalid.'),
        'SL_E_INVALID_OFFLINE_BLOB' : (0xC004C329, 'Genuine Validation determined the offline data blob is invalid.'),
        'SL_E_OFFLINE_VALIDATION_BLOB_PARAM_NOT_FOUND' : (0xC004C32A, 'Genuine Validation determined the offline data blob parameter is invalid.'),
        'SL_E_INVALID_OSVERSION_TEMPLATEID' : (0xC004C32B, 'Genuine Validation determined the validation template identifier is invalid for this version of the Windows operating system.'),
        'SL_E_OFFLINE_GENUINE_BLOB_REVOKED' : (0xC004C32C, 'Genuine Validation determined the offline genuine blob is revoked.'),
        'SL_E_OFFLINE_GENUINE_BLOB_NOT_FOUND' : (0xC004C32D, 'Genuine Validation determined the offline genuine blob is not found.'),
        'SL_E_CHPA_MSCH_RESPONSE_NOT_AVAILABLE_VGA' : (0xC004C3FF, 'The activation server determined the VGA service response is not available in the expected format.'),
        'SL_E_INVALID_OS_FOR_PRODUCT_KEY' : (0xC004C401, 'Genuine Validation determined the product key is invalid for this version of the Windows operating system.'),
        'SL_E_INVALID_FILE_HASH' : (0xC004C4A1, 'Genuine Validation determined the file hash is invalid.'),
        'SL_E_VALIDATION_BLOCKED_PRODUCT_KEY' : (0xC004C4A2, 'Genuine Validation determined the product key has been blocked.'),
        'SL_E_MISMATCHED_KEY_TYPES' : (0xC004C4A4, 'Genuine Validation determined the product key type is invalid.'),
        'SL_E_VALIDATION_INVALID_PRODUCT_KEY' : (0xC004C4A5, 'Genuine Validation determined the product key is invalid.'),
        'SL_E_INVALID_OEM_OR_VOLUME_BINDING_DATA' : (0xC004C4A7, 'Genuine Validation determined the OEM or Volume binding data is invalid.'),
        'SL_E_INVALID_LICENSE_STATE' : (0xC004C4A8, 'Genuine Validation determined the license state is invalid.'),
        'SL_E_IP_LOCATION_FALIED' : (0xC004C4A9, 'Genuine Validation determined the specified product key has been blocked for this geographic location.'),
        'SL_E_SOFTMOD_EXPLOIT_DETECTED' : (0xC004C4AB, 'Genuine Validation detected Windows licensing exploits.'),
        'SL_E_INVALID_TOKEN_DATA' : (0xC004C4AC, 'Genuine Validation determined the token activation data is invalid.'),
        'SL_E_HEALTH_CHECK_FAILED_NEUTRAL_FILES' : (0xC004C4AD, 'Genuine Validation detected tampered Windows binaries.'),
        'SL_E_HEALTH_CHECK_FAILED_MUI_FILES' : (0xC004C4AE, 'Genuine Validation detected tampered Windows binaries.'),
        'SL_E_INVALID_AD_DATA' : (0xC004C4AF, 'Genuine Validation determined the active directory activation data is invalid.'),
        'SL_E_INVALID_RSDP_COUNT' : (0xC004C4B0, 'Genuine Validation detected Windows licensing exploits.'),
        'SL_E_ENGINE_DETECTED_EXPLOIT' : (0xC004C4B1, 'Genuine Validation detected Windows licensing exploits.'),
        'SL_E_NOTIFICATION_BREACH_DETECTED' : (0xC004C531, 'Genuine Validation detected Windows licensing exploits.'),
        'SL_E_NOTIFICATION_GRACE_EXPIRED' : (0xC004C532, 'Genuine Validation determined the license state is in notification due to expired grace.'),
        'SL_E_NOTIFICATION_OTHER_REASONS' : (0xC004C533, 'Genuine Validation determined the license state is in notification.'),
        'SL_E_NON_GENUINE_STATUS_LAST' : (0xC004C600, 'Genuine Validation determined your copy of Windows is not genuine.'),
        'SL_E_CHPA_BUSINESS_RULE_INPUT_NOT_FOUND' : (0xC004C700, 'The activation server reported that business rule cound not find required input.'),
        'SL_E_CHPA_NULL_VALUE_FOR_PROPERTY_NAME_OR_ID' : (0xC004C750, 'The activation server reported that NULL value specified for business property name and Id.'),
        'SL_E_CHPA_UNKNOWN_PROPERTY_NAME' : (0xC004C751, 'The activation server reported that property name specifies unknown property.'),
        'SL_E_CHPA_UNKNOWN_PROPERTY_ID' : (0xC004C752, 'The activation server reported that property Id specifies unknown property.'),
        'SL_E_CHPA_FAILED_TO_UPDATE_PRODUCTKEY_BINDING' : (0xC004C755, 'The activation server reported that it failed to update product key binding.'),
        'SL_E_CHPA_FAILED_TO_INSERT_PRODUCTKEY_BINDING' : (0xC004C756, 'The activation server reported that it failed to insert product key binding.'),
        'SL_E_CHPA_FAILED_TO_DELETE_PRODUCTKEY_BINDING' : (0xC004C757, 'The activation server reported that it failed to delete product key binding.'),
        'SL_E_CHPA_FAILED_TO_PROCESS_PRODUCT_KEY_BINDINGS_XML' : (0xC004C758, 'The activation server reported that it failed to process input XML for product key bindings.'),
        'SL_E_CHPA_FAILED_TO_INSERT_PRODUCT_KEY_PROPERTY' : (0xC004C75A, 'The activation server reported that it failed to insert product key property.'),
        'SL_E_CHPA_FAILED_TO_UPDATE_PRODUCT_KEY_PROPERTY' : (0xC004C75B, 'The activation server reported that it failed to update product key property.'),
        'SL_E_CHPA_FAILED_TO_DELETE_PRODUCT_KEY_PROPERTY' : (0xC004C75C, 'The activation server reported that it failed to delete product key property.'),
        'SL_E_CHPA_UNKNOWN_PRODUCT_KEY_TYPE' : (0xC004C764, 'The activation server reported that the product key type is unknown.'),
        'SL_E_CHPA_PRODUCT_KEY_BEING_USED' : (0xC004C770, 'The activation server reported that the product key type is being used by another user.'),
        'SL_E_CHPA_FAILED_TO_INSERT_PRODUCT_KEY_RECORD' : (0xC004C780, 'The activation server reported that it failed to insert product key record.'),
        'SL_E_CHPA_FAILED_TO_UPDATE_PRODUCT_KEY_RECORD' : (0xC004C781, 'The activation server reported that it failed to update product key record.'),
        'SL_REMAPPING_SP_PUB_API_INVALID_LICENSE' : (0xC004D000, ''),
        'SL_REMAPPING_SP_PUB_API_INVALID_ALGORITHM_TYPE' : (0xC004D009, ''),
        'SL_REMAPPING_SP_PUB_API_TOO_MANY_LOADED_ENVIRONMENTS' : (0xC004D00C, ''),
        'SL_REMAPPING_SP_PUB_API_BAD_GET_INFO_QUERY' : (0xC004D012, ''),
        'SL_REMAPPING_SP_PUB_API_INVALID_KEY_LENGTH' : (0xC004D055, ''),
        'SL_REMAPPING_SP_PUB_API_NO_AES_PROVIDER' : (0xC004D073, ''),
        'SL_REMAPPING_SP_PUB_API_HANDLE_NOT_COMMITED' : (0xC004D081, 'The handle was used before calling SPCommit with it.'),
        'SL_REMAPPING_SP_PUB_GENERAL_NOT_INITIALIZED' : (0xC004D101, 'The security processor reported an initialization error.'),
        'SL_REMAPPING_SP_STATUS_SYSTEM_TIME_SKEWED' : (0x8004D102, 'The security processor reported that the machine time is inconsistent with the trusted time.'),
        'SL_REMAPPING_SP_STATUS_GENERIC_FAILURE' : (0xC004D103, 'The security processor reported that an error has occurred.'),
        'SL_REMAPPING_SP_STATUS_INVALIDARG' : (0xC004D104, 'The security processor reported that invalid data was used.'),
        'SL_REMAPPING_SP_STATUS_ALREADY_EXISTS' : (0xC004D105, 'The security processor reported that the value already exists.'),
        'SL_REMAPPING_SP_STATUS_INSUFFICIENT_BUFFER' : (0xC004D107, 'The security processor reported that an insufficient buffer was used.'),
        'SL_REMAPPING_SP_STATUS_INVALIDDATA' : (0xC004D108, 'The security processor reported that invalid data was used.'),
        'SL_REMAPPING_SP_STATUS_INVALID_SPAPI_CALL' : (0xC004D109, 'The security processor reported that an invalid call was made.'),
        'SL_REMAPPING_SP_STATUS_INVALID_SPAPI_VERSION' : (0xC004D10A, 'The security processor reported a version mismatch error.'),
        'SL_REMAPPING_SP_STATUS_DEBUGGER_DETECTED' : (0x8004D10B, 'The security processor cannot operate while a debugger is attached.'),
        'SL_REMAPPING_SP_STATUS_NO_MORE_DATA' : (0xC004D10C, 'No more data is available.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_KEYLENGTH' : (0xC004D201, 'The length of the cryptopgraphic key material/blob is invalid.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_BLOCKLENGTH' : (0xC004D202, 'The block length is not correct for this algorithm.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_CIPHER' : (0xC004D203, 'The Cryptopgrahic cipher/algorithm type is invalid.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_CIPHERMODE' : (0xC004D204, 'The specified cipher mode is invalid. For example both encrypt and decrypt cannot be specified for symmetric keys.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_UNKNOWN_PROVIDERID' : (0xC004D205, 'The SPAPIID for the specified Cryptographic Provider is unknown.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_UNKNOWN_KEYID' : (0xC004D206, 'The SPAPIID for the specified Cryptographic Key (type) is unknown.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_UNKNOWN_HASHID' : (0xC004D207, 'The SPAPIID for the specified Cryptographic Hash is unknown.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_UNKNOWN_ATTRIBUTEID' : (0xC004D208, 'The SPAPIID for the specified Cryptographic Attribute is unknown.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_HASH_FINALIZED' : (0xC004D209, 'The hash object has been finalized and can no longer be updated.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_KEY_NOT_AVAILABLE' : (0xC004D20A, 'The key is not available within the current state.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_KEY_NOT_FOUND' : (0xC004D20B, 'The key does not exist. It may not have have been created yet.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_NOT_BLOCK_ALIGNED' : (0xC004D20C, "The data length is not a multiple of the algorithm's block length."),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_SIGNATURELENGTH' : (0xC004D20D, 'The length of the signature is not valid.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_SIGNATURE' : (0xC004D20E, 'The signature does not correlate with the comparison hash.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_BLOCK' : (0xC004D20F, 'The RSA block is not valid.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_FORMAT' : (0xC004D210, 'The format of the RSA block is not valid.'),
        'SL_REMAPPING_SP_PUB_CRYPTO_INVALID_PADDING' : (0xC004D211, 'The CBC padding is not valid.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED' : (0xC004D301, 'The security processor reported that the trusted data store was tampered.'),
        'SL_REMAPPING_SP_PUB_TS_REARMED' : (0xC004D302, 'The security processor reported that the trusted data store was rearmed.'),
        'SL_REMAPPING_SP_PUB_TS_RECREATED' : (0xC004D303, 'The security processor reported that the trusted store has been recreated.'),
        'SL_REMAPPING_SP_PUB_TS_ENTRY_KEY_NOT_FOUND' : (0xC004D304, 'The security processor reported that entry key was not found in the trusted data store.'),
        'SL_REMAPPING_SP_PUB_TS_ENTRY_KEY_ALREADY_EXISTS' : (0xC004D305, 'The security processor reported that the entry key already exists in the trusted data store.'),
        'SL_REMAPPING_SP_PUB_TS_ENTRY_KEY_SIZE_TOO_BIG' : (0xC004D306, 'The security processor reported that the entry key is too big to fit in the trusted data store.'),
        'SL_REMAPPING_SP_PUB_TS_MAX_REARM_REACHED' : (0xC004D307, 'The security processor reported that the maximum allowed number of re-arms has been exceeded. You must re-install the OS before trying to re-arm again.'),
        'SL_REMAPPING_SP_PUB_TS_DATA_SIZE_TOO_BIG' : (0xC004D308, 'The security processor has reported that entry data size is too big to fit in the trusted data store.'),
        'SL_REMAPPING_SP_PUB_TS_INVALID_HW_BINDING' : (0xC004D309, 'The security processor has reported that the machine has gone out of hardware tolerance.'),
        'SL_REMAPPING_SP_PUB_TIMER_ALREADY_EXISTS' : (0xC004D30A, 'The security processor has reported that the secure timer already exists.'),
        'SL_REMAPPING_SP_PUB_TIMER_NOT_FOUND' : (0xC004D30B, 'The security processor has reported that the secure timer was not found.'),
        'SL_REMAPPING_SP_PUB_TIMER_EXPIRED' : (0xC004D30C, 'The security processor has reported that the secure timer has expired.'),
        'SL_REMAPPING_SP_PUB_TIMER_NAME_SIZE_TOO_BIG' : (0xC004D30D, 'The security processor has reported that the secure timer name is too long.'),
        'SL_REMAPPING_SP_PUB_TS_FULL' : (0xC004D30E, 'The security processor reported that the trusted data store is full.'),
        'SL_REMAPPING_SP_PUB_TRUSTED_TIME_OK' : (0x4004D30F, 'Trusted time is already up-to-date.'),
        'SL_REMAPPING_SP_PUB_TS_ENTRY_READ_ONLY' : (0xC004D310, 'Read-only entry cannot be modified.'),
        'SL_REMAPPING_SP_PUB_TIMER_READ_ONLY' : (0xC004D311, 'Read-only timer cannot be modified.'),
        'SL_REMAPPING_SP_PUB_TS_ATTRIBUTE_READ_ONLY' : (0xC004D312, 'Read-only attribute cannot be modified.'),
        'SL_REMAPPING_SP_PUB_TS_ATTRIBUTE_NOT_FOUND' : (0xC004D313, 'Attribute not found.'),
        'SL_REMAPPING_SP_PUB_TS_ACCESS_DENIED' : (0xC004D314, 'Trusted Store access denied.'),
        'SL_REMAPPING_SP_PUB_TS_NAMESPACE_NOT_FOUND' : (0xC004D315, 'Namespace not found.'),
        'SL_REMAPPING_SP_PUB_TS_NAMESPACE_IN_USE' : (0xC004D316, 'Namespace in use.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_BREADCRUMB_LOAD_INVALID' : (0xC004D317, 'Trusted store tampered.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_BREADCRUMB_GENERATION' : (0xC004D318, 'Trusted store tampered.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_INVALID_DATA' : (0xC004D319, 'Trusted store tampered.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_NO_DATA' : (0xC004D31A, 'Trusted store tampered.'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_DATA_BREADCRUMB_MISMATCH' : (0xC004D31B, 'Trusted store tampered'),
        'SL_REMAPPING_SP_PUB_TS_TAMPERED_DATA_VERSION_MISMATCH' : (0xC004D31C, 'Trusted store tampered.'),
        'SL_REMAPPING_SP_PUB_TAMPER_MODULE_AUTHENTICATION' : (0xC004D401, 'The security processor reported a system file mismatch error.'),
        'SL_REMAPPING_SP_PUB_TAMPER_SECURITY_PROCESSOR_PATCHED' : (0xC004D402, 'The security processor reported a system file mismatch error.'),
        'SL_REMAPPING_SP_PUB_KM_CACHE_TAMPER' : (0xC004D501, 'The security processor reported an error with the kernel data.'),
        'SL_REMAPPING_SP_PUB_KM_CACHE_TAMPER_RESTORE_FAILED' : (0xC004D502, 'Kernel Mode Cache is tampered and the restore attempt failed.'),
        'SL_REMAPPING_SP_PUB_KM_CACHE_IDENTICAL' : (0x4004D601, 'Kernel Mode Cache was not changed.'),
        'SL_REMAPPING_SP_PUB_KM_CACHE_POLICY_CHANGED' : (0x4004D602, 'Reboot-requiring policies have changed.'),
        'SL_REMAPPING_SP_STATUS_PUSHKEY_CONFLICT' : (0xC004D701, 'External decryption key was already set for specified feature.'),
        'SL_REMAPPING_SP_PUB_PROXY_SOFT_TAMPER' : (0xC004D702, 'Error occured during proxy execution'),
        'SL_E_INVALID_CONTEXT' : (0xC004E001, 'The Software Licensing Service determined that the specified context is invalid.'),
        'SL_E_TOKEN_STORE_INVALID_STATE' : (0xC004E002, 'The Software Licensing Service reported that the license store contains inconsistent data.'),
        'SL_E_EVALUATION_FAILED' : (0xC004E003, 'The Software Licensing Service reported that license evaluation failed.'),
        'SL_E_NOT_EVALUATED' : (0xC004E004, 'The Software Licensing Service reported that the license has not been evaluated.'),
        'SL_E_NOT_ACTIVATED' : (0xC004E005, 'The Software Licensing Service reported that the license is not activated.'),
        'SL_E_INVALID_GUID' : (0xC004E006, 'The Software Licensing Service reported that the license contains invalid data.'),
        'SL_E_TOKSTO_TOKEN_NOT_FOUND' : (0xC004E007, 'The Software Licensing Service reported that the license store does not contain the requested license.'),
        'SL_E_TOKSTO_NO_PROPERTIES' : (0xC004E008, 'The Software Licensing Service reported that the license property is invalid.'),
        'SL_E_TOKSTO_NOT_INITIALIZED' : (0xC004E009, 'The Software Licensing Service reported that the license store is not initialized.'),
        'SL_E_TOKSTO_ALREADY_INITIALIZED' : (0xC004E00A, 'The Software Licensing Service reported that the license store is already initialized.'),
        'SL_E_TOKSTO_NO_ID_SET' : (0xC004E00B, 'The Software Licensing Service reported that the license property is invalid.'),
        'SL_E_TOKSTO_CANT_CREATE_FILE' : (0xC004E00C, 'The Software Licensing Service reported that the license could not be opened or created.'),
        'SL_E_TOKSTO_CANT_WRITE_TO_FILE' : (0xC004E00D, 'The Software Licensing Service reported that the license could not be written.'),
        'SL_E_TOKSTO_CANT_READ_FILE' : (0xC004E00E, 'The Software Licensing Service reported that the license store could not read the license file.'),
        'SL_E_TOKSTO_CANT_PARSE_PROPERTIES' : (0xC004E00F, 'The Software Licensing Service reported that the license property is corrupted.'),
        'SL_E_TOKSTO_PROPERTY_NOT_FOUND' : (0xC004E010, 'The Software Licensing Service reported that the license property is missing.'),
        'SL_E_TOKSTO_INVALID_FILE' : (0xC004E011, 'The Software Licensing Service reported that the license store contains an invalid license file.'),
        'SL_E_TOKSTO_CANT_CREATE_MUTEX' : (0xC004E012, 'The Software Licensing Service reported that the license store failed to start synchronization properly.'),
        'SL_E_TOKSTO_CANT_ACQUIRE_MUTEX' : (0xC004E013, 'The Software Licensing Service reported that the license store failed to synchronize properly.'),
        'SL_E_TOKSTO_NO_TOKEN_DATA' : (0xC004E014, 'The Software Licensing Service reported that the license property is invalid.'),
        'SL_E_EUL_CONSUMPTION_FAILED' : (0xC004E015, 'The Software Licensing Service reported that license consumption failed.'),
        'SL_E_PKEY_INVALID_CONFIG' : (0xC004E016, 'The Software Licensing Service reported that the product key is invalid.'),
        'SL_E_PKEY_INVALID_UNIQUEID' : (0xC004E017, 'The Software Licensing Service reported that the product key is invalid.'),
        'SL_E_PKEY_INVALID_ALGORITHM' : (0xC004E018, 'The Software Licensing Service reported that the product key is invalid.'),
        'SL_E_PKEY_INTERNAL_ERROR' : (0xC004E019, 'The Software Licensing Service determined that validation of the specified product key failed.'),
        'SL_E_LICENSE_INVALID_ADDON_INFO' : (0xC004E01A, 'The Software Licensing Service reported that invalid add-on information was found.'),
        'SL_E_HWID_ERROR' : (0xC004E01B, 'The Software Licensing Service reported that not all hardware information could be collected.'),
        'SL_E_PKEY_INVALID_KEYCHANGE1' : (0xC004E01C, 'This evaluation product key is no longer valid.'),
        'SL_E_PKEY_INVALID_KEYCHANGE2' : (0xC004E01D, 'The new product key cannot be used on this installation of Windows. Type a different product key. (CD-AB)'),
        'SL_E_PKEY_INVALID_KEYCHANGE3' : (0xC004E01E, 'The new product key cannot be used on this installation of Windows. Type a different product key. (AB-AB)'),
        'SL_E_POLICY_OTHERINFO_MISMATCH' : (0xC004E020, 'The Software Licensing Service reported that there is a mismatched between a policy value and information stored in the OtherInfo section.'),
        'SL_E_PRODUCT_UNIQUENESS_GROUP_ID_INVALID' : (0xC004E021, 'The Software Licensing Service reported that the Genuine information contained in the license is not consistent.'),
        'SL_E_SECURE_STORE_ID_MISMATCH' : (0xC004E022, 'The Software Licensing Service reported that the secure store id value in license does not match with the current value.'),
        'SL_E_INVALID_RULESET_RULE' : (0xC004E023, 'The Software Licensing Service reported that the notification rules appear to be invalid.'),
        'SL_E_INVALID_CONTEXT_DATA' : (0xC004E024, 'The Software Licensing Service reported that the reported machine data appears to be invalid.'),
        'SL_E_INVALID_HASH' : (0xC004E025, 'The Software Licensing Service reported that the data hash does not correspond to the data.'),
        'SL_E_INVALID_USE_OF_ADD_ON_PKEY' : (0x8004E026, 'The Software Licensing Service reported that a valid product key for an add-on sku was entered where a Windows product key was expected.'),
        'SL_E_WINDOWS_VERSION_MISMATCH' : (0xC004E027, 'The Software Licensing Service reported that the version of SPPSvc does not match the policy.'),
        'SL_E_ACTIVATION_IN_PROGRESS' : (0xC004E028, 'The Software Licensing Service reported that there is another activation attempt in progress for this sku. Please wait for that attempt to complete before trying again.'),
        'SL_E_STORE_UPGRADE_TOKEN_REQUIRED' : (0xC004E029, 'The Software Licensing Service reported that the activated license requires a corresponding Store upgrade license in order to work. Please visit the Store to purchase a new license or re-download an existing one.'),
        'SL_E_STORE_UPGRADE_TOKEN_WRONG_EDITION' : (0xC004E02A, 'The Software Licensing Service reported that the Store upgrade license is not enabled for the current OS edition. Please visit the Store to purchase the appropriate license.'),
        'SL_E_STORE_UPGRADE_TOKEN_WRONG_PID' : (0xC004E02B, 'The Software Licensing Service reported that the Store upgrade license does not match the current active product key. Please visit the Store to purchase a new license or re-download an existing one.'),
        'SL_E_STORE_UPGRADE_TOKEN_NOT_PRS_SIGNED' : (0xC004E02C, 'The Software Licensing Service reported that the Store upgrade license does not match the current signing level for the installed Operating System. Please visit the Store to purchase a new license or re-download an existing one.'),
        'SL_E_STORE_UPGRADE_TOKEN_WRONG_VERSION' : (0xC004E02D, 'The Software Licensing Service reported that the Store upgrade license does not enable the current version of the installed Operating System. Please visit the Store to purchase a new license or re-download an existing one.'),
        'SL_E_STORE_UPGRADE_TOKEN_NOT_AUTHORIZED' : (0xC004E02E, 'The Software Licensing Service reported that the Store upgrade license could not be authorized. Please visit the Store to purchase a new license or re-download an existing one.'),
        'SL_E_SFS_INVALID_FS_VERSION' : (0x8004E101, 'The Software Licensing Service reported that the Token Store file version is invalid.'),
        'SL_E_SFS_INVALID_FD_TABLE' : (0x8004E102, 'The Software Licensing Service reported that the Token Store contains an invalid descriptor table.'),
        'SL_E_SFS_INVALID_SYNC' : (0x8004E103, 'The Software Licensing Service reported that the Token Store contains a token with an invalid header/footer.'),
        'SL_E_SFS_BAD_TOKEN_NAME' : (0x8004E104, 'The Software Licensing Service reported that a Token Store token has an invalid name.'),
        'SL_E_SFS_BAD_TOKEN_EXT' : (0x8004E105, 'The Software Licensing Service reported that a Token Store token has an invalid extension.'),
        'SL_E_SFS_DUPLICATE_TOKEN_NAME' : (0x8004E106, 'The Software Licensing Service reported that the Token Store contains a duplicate token.'),
        'SL_E_SFS_TOKEN_SIZE_MISMATCH' : (0x8004E107, 'The Software Licensing Service reported that a token in the Token Store has a size mismatch.'),
        'SL_E_SFS_INVALID_TOKEN_DATA_HASH' : (0x8004E108, 'The Software Licensing Service reported that a token in the Token Store contains an invalid hash.'),
        'SL_E_SFS_FILE_READ_ERROR' : (0x8004E109, 'The Software Licensing Service reported that the Token Store was unable to read a token.'),
        'SL_E_SFS_FILE_WRITE_ERROR' : (0x8004E10A, 'The Software Licensing Service reported that the Token Store was unable to write a token.'),
        'SL_E_SFS_INVALID_FILE_POSITION' : (0x8004E10B, 'The Software Licensing Service reported that the Token Store attempted an invalid file operation.'),
        'SL_E_SFS_NO_ACTIVE_TRANSACTION' : (0x8004E10C, 'The Software Licensing Service reported that there is no active transaction.'),
        'SL_E_SFS_INVALID_FS_HEADER' : (0x8004E10D, 'The Software Licensing Service reported that the Token Store file header is invalid.'),
        'SL_E_SFS_INVALID_TOKEN_DESCRIPTOR' : (0x8004E10E, 'The Software Licensing Service reported that a Token Store token descriptor is invalid.'),
        'SL_E_INTERNAL_ERROR' : (0xC004F001, 'The Software Licensing Service reported an internal error.'),
        'SL_E_RIGHT_NOT_CONSUMED' : (0xC004F002, 'The Software Licensing Service reported that rights consumption failed.'),
        'SL_E_USE_LICENSE_NOT_INSTALLED' : (0xC004F003, 'The Software Licensing Service reported that the required license could not be found.'),
        'SL_E_MISMATCHED_PKEY_RANGE' : (0xC004F004, 'The Software Licensing Service reported that the product key does not match the range defined in the license.'),
        'SL_E_MISMATCHED_PID' : (0xC004F005, 'The Software Licensing Service reported that the product key does not match the product key for the license.'),
        'SL_E_EXTERNAL_SIGNATURE_NOT_FOUND' : (0xC004F006, 'The Software Licensing Service reported that the signature file for the license is not available.'),
        'SL_E_RAC_NOT_AVAILABLE' : (0xC004F007, 'The Software Licensing Service reported that the license could not be found.'),
        'SL_E_SPC_NOT_AVAILABLE' : (0xC004F008, 'The Software Licensing Service reported that the license could not be found.'),
        'SL_E_GRACE_TIME_EXPIRED' : (0xC004F009, 'The Software Licensing Service reported that the grace period expired.'),
        'SL_E_MISMATCHED_APPID' : (0xC004F00A, 'The Software Licensing Service reported that the application ID does not match the application ID for the license.'),
        'SL_E_NO_PID_CONFIG_DATA' : (0xC004F00B, 'The Software Licensing Service reported that the product identification data is not available.'),
        'SL_I_OOB_GRACE_PERIOD' : (0x4004F00C, 'The Software Licensing Service reported that the application is running within the valid grace period.'),
        'SL_I_OOT_GRACE_PERIOD' : (0x4004F00D, 'The Software Licensing Service reported that the application is running within the valid out of tolerance grace period.'),
        'SL_E_MISMATCHED_SECURITY_PROCESSOR' : (0xC004F00E, 'The Software Licensing Service determined that the license could not be used by the current version of the security processor component.'),
        'SL_E_OUT_OF_TOLERANCE' : (0xC004F00F, 'The Software Licensing Service reported that the hardware ID binding is beyond the level of tolerance.'),
        'SL_E_INVALID_PKEY' : (0xC004F010, 'The Software Licensing Service reported that the product key is invalid.'),
        'SL_E_LICENSE_FILE_NOT_INSTALLED' : (0xC004F011, 'The Software Licensing Service reported that the license file is not installed.'),
        'SL_E_VALUE_NOT_FOUND' : (0xC004F012, 'The Software Licensing Service reported that the call has failed because the value for the input key was not found.'),
        'SL_E_RIGHT_NOT_GRANTED' : (0xC004F013, 'The Software Licensing Service determined that there is no permission to run the software.'),
        'SL_E_PKEY_NOT_INSTALLED' : (0xC004F014, 'The Software Licensing Service reported that the product key is not available.'),
        'SL_E_PRODUCT_SKU_NOT_INSTALLED' : (0xC004F015, 'The Software Licensing Service reported that the license is not installed.'),
        'SL_E_NOT_SUPPORTED' : (0xC004F016, 'The Software Licensing Service determined that the request is not supported.'),
        'SL_E_PUBLISHING_LICENSE_NOT_INSTALLED' : (0xC004F017, 'The Software Licensing Service reported that the license is not installed.'),
        'SL_E_LICENSE_SERVER_URL_NOT_FOUND' : (0xC004F018, 'The Software Licensing Service reported that the license does not contain valid location data for the activation server.'),
        'SL_E_INVALID_EVENT_ID' : (0xC004F019, 'The Software Licensing Service determined that the requested event ID is invalid.'),
        'SL_E_EVENT_NOT_REGISTERED' : (0xC004F01A, 'The Software Licensing Service determined that the requested event is not registered with the service.'),
        'SL_E_EVENT_ALREADY_REGISTERED' : (0xC004F01B, 'The Software Licensing Service reported that the event ID is already registered.'),
        'SL_E_DECRYPTION_LICENSES_NOT_AVAILABLE' : (0xC004F01C, 'The Software Licensing Service reported that the license is not installed.'),
        'SL_E_LICENSE_SIGNATURE_VERIFICATION_FAILED' : (0xC004F01D, 'The Software Licensing Service reported that the verification of the license failed.'),
        'SL_E_DATATYPE_MISMATCHED' : (0xC004F01E, 'The Software Licensing Service determined that the input data type does not match the data type in the license.'),
        'SL_E_INVALID_LICENSE' : (0xC004F01F, 'The Software Licensing Service determined that the license is invalid.'),
        'SL_E_INVALID_PACKAGE' : (0xC004F020, 'The Software Licensing Service determined that the license package is invalid.'),
        'SL_E_VALIDITY_TIME_EXPIRED' : (0xC004F021, 'The Software Licensing Service reported that the validity period of the license has expired.'),
        'SL_E_LICENSE_AUTHORIZATION_FAILED' : (0xC004F022, 'The Software Licensing Service reported that the license authorization failed.'),
        'SL_E_LICENSE_DECRYPTION_FAILED' : (0xC004F023, 'The Software Licensing Service reported that the license is invalid.'),
        'SL_E_WINDOWS_INVALID_LICENSE_STATE' : (0xC004F024, 'The Software Licensing Service reported that the license is invalid.'),
        'SL_E_LUA_ACCESSDENIED' : (0xC004F025, 'The Software Licensing Service reported that the action requires administrator privilege.'),
        'SL_E_PROXY_KEY_NOT_FOUND' : (0xC004F026, 'The Software Licensing Service reported that the required data is not found.'),
        'SL_E_TAMPER_DETECTED' : (0xC004F027, 'The Software Licensing Service reported that the license is tampered.'),
        'SL_E_POLICY_CACHE_INVALID' : (0xC004F028, 'The Software Licensing Service reported that the policy cache is invalid.'),
        'SL_E_INVALID_RUNNING_MODE' : (0xC004F029, 'The Software Licensing Service cannot be started in the current OS mode.'),
        'SL_E_SLP_NOT_SIGNED' : (0xC004F02A, 'The Software Licensing Service reported that the license is invalid.'),
        'SL_E_CIDIID_INVALID_DATA' : (0xC004F02C, 'The Software Licensing Service reported that the format for the offline activation data is incorrect.'),
        'SL_E_CIDIID_INVALID_VERSION' : (0xC004F02D, 'The Software Licensing Service determined that the version of the offline Confirmation ID (CID) is incorrect.'),
        'SL_E_CIDIID_VERSION_NOT_SUPPORTED' : (0xC004F02E, 'The Software Licensing Service determined that the version of the offline Confirmation ID (CID) is not supported.'),
        'SL_E_CIDIID_INVALID_DATA_LENGTH' : (0xC004F02F, 'The Software Licensing Service reported that the length of the offline Confirmation ID (CID) is incorrect.'),
        'SL_E_CIDIID_NOT_DEPOSITED' : (0xC004F030, 'The Software Licensing Service determined that the Installation ID (IID) or the Confirmation ID (CID) could not been saved.'),
        'SL_E_CIDIID_MISMATCHED' : (0xC004F031, 'The Installation ID (IID) and the Confirmation ID (CID) do not match. Please confirm the IID and reacquire a new CID if necessary.'),
        'SL_E_INVALID_BINDING_BLOB' : (0xC004F032, 'The Software Licensing Service determined that the binding data is invalid.'),
        'SL_E_PRODUCT_KEY_INSTALLATION_NOT_ALLOWED' : (0xC004F033, 'The Software Licensing Service reported that the product key is not allowed to be installed. Please see the eventlog for details.'),
        'SL_E_EUL_NOT_AVAILABLE' : (0xC004F034, 'The Software Licensing Service reported that the license could not be found or was invalid.'),
        'SL_E_VL_NOT_WINDOWS_SLP' : (0xC004F035, 'The Software Licensing Service reported that the computer could not be activated with a Volume license product key. Volume-licensed systems require upgrading from a qualifying operating system. Please contact your system administrator or use a different type of key.'),
        'SL_E_VL_NOT_ENOUGH_COUNT' : (0xC004F038, 'The Software Licensing Service reported that the product could not be activated. The count reported by your Key Management Service (KMS) is insufficient. Please contact your system administrator.'),
        'SL_E_VL_BINDING_SERVICE_NOT_ENABLED' : (0xC004F039, 'The Software Licensing Service reported that the product could not be activated. The Key Management Service (KMS) is not enabled.'),
        'SL_E_VL_INFO_PRODUCT_USER_RIGHT' : (0x4004F040, 'The Software Licensing Service reported that the product was activated but the owner should verify the Product Use Rights.'),
        'SL_E_VL_KEY_MANAGEMENT_SERVICE_NOT_ACTIVATED' : (0xC004F041, 'The Software Licensing Service determined that the Key Management Service (KMS) is not activated. KMS needs to be activated. Please contact system administrator.'),
        'SL_E_VL_KEY_MANAGEMENT_SERVICE_ID_MISMATCH' : (0xC004F042, 'The Software Licensing Service determined that the specified Key Management Service (KMS) cannot be used.'),
        'SL_E_PROXY_POLICY_NOT_UPDATED' : (0xC004F047, 'The Software Licensing Service reported that the proxy policy has not been updated.'),
        'SL_E_CIDIID_INVALID_CHECK_DIGITS' : (0xC004F04D, 'The Software Licensing Service determined that the Installation ID (IID) or the Confirmation ID (CID) is invalid.'),
        'SL_E_LICENSE_MANAGEMENT_DATA_NOT_FOUND' : (0xC004F04F, 'The Software Licensing Service reported that license management information was not found in the licenses.'),
        'SL_E_INVALID_PRODUCT_KEY' : (0xC004F050, 'The Software Licensing Service reported that the product key is invalid.'),
        'SL_E_BLOCKED_PRODUCT_KEY' : (0xC004F051, 'The Software Licensing Service reported that the product key is blocked.'),
        'SL_E_DUPLICATE_POLICY' : (0xC004F052, 'The Software Licensing Service reported that the licenses contain duplicated properties.'),
        'SL_E_MISSING_OVERRIDE_ONLY_ATTRIBUTE' : (0xC004F053, 'The Software Licensing Service determined that the license is invalid. The license contains an override policy that is not configured properly.'),
        'SL_E_LICENSE_MANAGEMENT_DATA_DUPLICATED' : (0xC004F054, 'The Software Licensing Service reported that license management information has duplicated data.'),
        'SL_E_BASE_SKU_NOT_AVAILABLE' : (0xC004F055, 'The Software Licensing Service reported that the base SKU is not available.'),
        'SL_E_VL_MACHINE_NOT_BOUND' : (0xC004F056, 'The Software Licensing Service reported that the product could not be activated using the Key Management Service (KMS).'),
        'SL_E_SLP_MISSING_ACPI_SLIC' : (0xC004F057, 'The Software Licensing Service reported that the computer BIOS is missing a required license.'),
        'SL_E_SLP_MISSING_SLP_MARKER' : (0xC004F058, 'The Software Licensing Service reported that the computer BIOS is missing a required license.'),
        'SL_E_SLP_BAD_FORMAT' : (0xC004F059, 'The Software Licensing Service reported that a license in the computer BIOS is invalid.'),
        'SL_E_INVALID_PACKAGE_VERSION' : (0xC004F060, 'The Software Licensing Service determined that the version of the license package is invalid.'),
        'SL_E_PKEY_INVALID_UPGRADE' : (0xC004F061, 'The Software Licensing Service determined that this specified product key can only be used for upgrading, not for clean installations.'),
        'SL_E_ISSUANCE_LICENSE_NOT_INSTALLED' : (0xC004F062, 'The Software Licensing Service reported that a required license could not be found.'),
        'SL_E_SLP_OEM_CERT_MISSING' : (0xC004F063, 'The Software Licensing Service reported that the computer is missing a required OEM license.'),
        'SL_E_NONGENUINE_GRACE_TIME_EXPIRED' : (0xC004F064, 'The Software Licensing Service reported that the non-genuine grace period expired.'),
        'SL_I_NONGENUINE_GRACE_PERIOD' : (0x4004F065, 'The Software Licensing Service reported that the application is running within the valid non-genuine grace period.'),
        'SL_E_DEPENDENT_PROPERTY_NOT_SET' : (0xC004F066, 'The Software Licensing Service reported that the genuine information property can not be set before dependent property been set.'),
        'SL_E_NONGENUINE_GRACE_TIME_EXPIRED_2' : (0xC004F067, 'The Software Licensing Service reported that the non-genuine grace period expired (type 2).'),
        'SL_I_NONGENUINE_GRACE_PERIOD_2' : (0x4004F068, 'The Software Licensing Service reported that the application is running within the valid non-genuine grace period (type 2).'),
        'SL_E_MISMATCHED_PRODUCT_SKU' : (0xC004F069, 'The Software Licensing Service reported that the product SKU is not found.'),
        'SL_E_OPERATION_NOT_ALLOWED' : (0xC004F06A, 'The Software Licensing Service reported that the requested operation is not allowed.'),
        'SL_E_VL_KEY_MANAGEMENT_SERVICE_VM_NOT_SUPPORTED' : (0xC004F06B, 'The Software Licensing Service determined that it is running in a virtual machine. The Key Management Service (KMS) is not supported in this mode.'),
        'SL_E_VL_INVALID_TIMESTAMP' : (0xC004F06C, 'The Software Licensing Service reported that the product could not be activated. The Key Management Service (KMS) determined that the request timestamp is invalid.'),
        'SL_E_PLUGIN_INVALID_MANIFEST' : (0xC004F071, 'The Software Licensing Service reported that the plug-in manifest file is incorrect.'),
        'SL_E_APPLICATION_POLICIES_MISSING' : (0xC004F072, 'The Software Licensing Service reported that the license policies for fast query could not be found.'),
        'SL_E_APPLICATION_POLICIES_NOT_LOADED' : (0xC004F073, 'The Software Licensing Service reported that the license policies for fast query have not been loaded.'),
        'SL_E_VL_BINDING_SERVICE_UNAVAILABLE' : (0xC004F074, 'The Software Licensing Service reported that the product could not be activated. No Key Management Service (KMS) could be contacted. Please see the Application Event Log for additional information.'),
        'SL_E_SERVICE_STOPPING' : (0xC004F075, 'The Software Licensing Service reported that the operation cannot be completed because the service is stopping.'),
        'SL_E_PLUGIN_NOT_REGISTERED' : (0xC004F076, 'The Software Licensing Service reported that the requested plug-in cannot be found.'),
        'SL_E_AUTHN_WRONG_VERSION' : (0xC004F077, 'The Software Licensing Service determined incompatible version of authentication data.'),
        'SL_E_AUTHN_MISMATCHED_KEY' : (0xC004F078, 'The Software Licensing Service reported that the key is mismatched.'),
        'SL_E_AUTHN_CHALLENGE_NOT_SET' : (0xC004F079, 'The Software Licensing Service reported that the authentication data is not set.'),
        'SL_E_AUTHN_CANT_VERIFY' : (0xC004F07A, 'The Software Licensing Service reported that the verification could not be done.'),
        'SL_E_SERVICE_RUNNING' : (0xC004F07B, 'The requested operation is unavailable while the Software Licensing Service is running.'),
        'SL_E_SLP_INVALID_MARKER_VERSION' : (0xC004F07C, 'The Software Licensing Service determined that the version of the computer BIOS is invalid.'),
        'SL_E_INVALID_PRODUCT_KEY_TYPE' : (0xC004F07D, 'The Software Licensing Service reported that the product key cannot be used for this type of activation.'),
        'SL_E_CIDIID_MISMATCHED_PKEY' : (0xC004F07E, 'The Installation ID (IID) and the Confirmation ID (CID) do not match the product key.'),
        'SL_E_CIDIID_NOT_BOUND' : (0xC004F07F, 'The Installation ID (IID) and the Confirmation ID (CID) are not bound to the current environment.'),
        'SL_E_LICENSE_NOT_BOUND' : (0xC004F080, 'The Software Licensing Service reported that the license is not bound to the current environment.'),
        'SL_E_VL_AD_AO_NOT_FOUND' : (0xC004F081, 'The Software Licensing Service reported that the Active Directory Activation Object could not be found or was invalid.'),
        'SL_E_VL_AD_AO_NAME_TOO_LONG' : (0xC004F082, 'The Software Licensing Service reported that the name specified for the Active Directory Activation Object is too long.'),
        'SL_E_VL_AD_SCHEMA_VERSION_NOT_SUPPORTED' : (0xC004F083, 'The Software Licensing Service reported that Active Directory-Based Activation is not supported in the current Active Directory schema.'),
        'SL_E_NOT_GENUINE' : (0xC004F200, 'The Software Licensing Service reported that current state is not genuine.'),
        'SL_E_EDITION_MISMATCHED' : (0xC004F210, 'The Software Licensing Service reported that the license edition does match the computer edition.'),
        'SL_E_TKA_CHALLENGE_EXPIRED' : (0xC004F301, 'The Software Licensing Service reported that the product could not be activated. The token-based activation challenge has expired.'),
        'SL_E_TKA_SILENT_ACTIVATION_FAILURE' : (0xC004F302, 'The Software Licensing Service reported that Silent Activation failed. The Software Licensing Service reported that there are no certificates found in the system that could activate the product without user interaction.'),
        'SL_E_TKA_INVALID_CERT_CHAIN' : (0xC004F303, 'The Software Licensing Service reported that the certificate chain could not be built or failed validation.'),
        'SL_E_TKA_GRANT_NOT_FOUND' : (0xC004F304, 'The Software Licensing Service reported that required license could not be found.'),
        'SL_E_TKA_CERT_NOT_FOUND' : (0xC004F305, 'The Software Licensing Service reported that there are no certificates found in the system that could activate the product.'),
        'SL_E_TKA_INVALID_SKU_ID' : (0xC004F306, 'The Software Licensing Service reported that this software edition does not support token-based activation.'),
        'SL_E_TKA_INVALID_BLOB' : (0xC004F307, 'The Software Licensing Service reported that the product could not be activated. Activation data is invalid.'),
        'SL_E_TKA_TAMPERED_CERT_CHAIN' : (0xC004F308, 'The Software Licensing Service reported that the product could not be activated. Activation data is tampered.'),
        'SL_E_TKA_CHALLENGE_MISMATCH' : (0xC004F309, 'The Software Licensing Service reported that the product could not be activated. Activation challenge and response do not match.'),
        'SL_E_TKA_INVALID_CERTIFICATE' : (0xC004F30A, 'The Software Licensing Service reported that the product could not be activated. The certificate does not match the conditions in the license.'),
        'SL_E_TKA_INVALID_SMARTCARD' : (0xC004F30B, 'The Software Licensing Service reported that the inserted smartcard could not be used to activate the product.'),
        'SL_E_TKA_FAILED_GRANT_PARSING' : (0xC004F30C, 'The Software Licensing Service reported that the token-based activation license content is invalid.'),
        'SL_E_TKA_INVALID_THUMBPRINT' : (0xC004F30D, 'The Software Licensing Service reported that the product could not be activated. The thumbprint is invalid.'),
        'SL_E_TKA_THUMBPRINT_CERT_NOT_FOUND' : (0xC004F30E, 'The Software Licensing Service reported that the product could not be activated. The thumbprint does not match any certificate.'),
        'SL_E_TKA_CRITERIA_MISMATCH' : (0xC004F30F, 'The Software Licensing Service reported that the product could not be activated. The certificate does not match the criteria specified in the issuance license.'),
        'SL_E_TKA_TPID_MISMATCH' : (0xC004F310, 'The Software Licensing Service reported that the product could not be activated. The certificate does not match the trust point identifier (TPID) specified in the issuance license.'),
        'SL_E_TKA_SOFT_CERT_DISALLOWED' : (0xC004F311, 'The Software Licensing Service reported that the product could not be activated. A soft token cannot be used for activation.'),
        'SL_E_TKA_SOFT_CERT_INVALID' : (0xC004F312, 'The Software Licensing Service reported that the product could not be activated. The certificate cannot be used because its private key is exportable.'),
        'SL_E_TKA_CERT_CNG_NOT_AVAILABLE' : (0xC004F313, 'The Software Licensing Service reported that the CNG encryption library could not be loaded. The current certificate may not be available on this version of Windows.'),
        'E_RM_UNKNOWN_ERROR' : (0xC004FC03, 'A networking problem has occurred while activating your copy of Windows.'),
        'SL_I_TIMEBASED_VALIDITY_PERIOD' : (0x4004FC04, 'The Software Licensing Service reported that the application is running within the timebased validity period.'),
        'SL_I_PERPETUAL_OOB_GRACE_PERIOD' : (0x4004FC05, 'The Software Licensing Service reported that the application has a perpetual grace period.'),
        'SL_I_TIMEBASED_EXTENDED_GRACE_PERIOD' : (0x4004FC06, 'The Software Licensing Service reported that the application is running within the valid extended grace period.'),
        'SL_E_VALIDITY_PERIOD_EXPIRED' : (0xC004FC07, 'The Software Licensing Service reported that the validity period expired.'),
        'SL_E_IA_THROTTLE_LIMIT_EXCEEDED' : (0xC004FD00, "You've reached the request limit for automatic virtual machine activation. Try again later."),
        'SL_E_IA_INVALID_VIRTUALIZATION_PLATFORM' : (0xC004FD01, "Windows isn't running on a supported Microsoft Hyper-V virtualization platform."),
        'SL_E_IA_PARENT_PARTITION_NOT_ACTIVATED' : (0xC004FD02, "Windows isn't activated on the host machine. Please contact your system administrator."),
        'SL_E_IA_ID_MISMATCH' : (0xC004FD03, "The host machine can't activate the edition of Windows on the virtual machine."),
        'SL_E_IA_MACHINE_NOT_BOUND' : (0xC004FD04, "Windows isn't activated."),
        'SL_E_TAMPER_RECOVERY_REQUIRES_ACTIVATION' : (0xC004FE00, 'The Software Licensing Service reported that activation is required to recover from tampering of SL Service trusted store.'),
        }
