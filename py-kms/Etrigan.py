#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import atexit
import errno
import os
import sys
import time
import signal
import logging
import argparse
from collections.abc import Sequence

__version__             = "0.1"
__license__             = "MIT License"
__author__              = u"Matteo ℱan <SystemRage@protonmail.com>"
__copyright__           = "© Copyright 2020"
__url__                 = "https://github.com/SystemRage/Etrigan"
__description__         = "Etrigan: a python daemonizer that rocks."


class Etrigan(object):
        """
        Daemonizer based on double-fork method
        --------------------------------------
        Each option can be passed as a keyword argument or modified by assigning
        to an attribute on the instance:
        
        jasonblood = Etrigan(pidfile,
                             argument_example_1 = foo,
                             argument_example_2 = bar)
        
        that is equivalent to:
        
        jasonblood = Etrigan(pidfile)
        jasonblood.argument_example_1 = foo
        jasonblood.argument_example_2 = bar

        Object constructor expects always `pidfile` argument.
        `pidfile`
                Path to the pidfile.
        
        The following other options are defined:
        `stdin`
        `stdout`
        `stderr`
                :Default: `os.devnull`
                        File objects used as the new file for the standard I/O streams
                        `sys.stdin`, `sys.stdout`, and `sys.stderr` respectively.
                        
        `funcs_to_daemonize`
                :Default: `[]`
                        Define a list of your custom functions
                        which will be executed after daemonization.
                        If None, you have to subclass Etrigan `run` method.
                        Note that these functions can return elements that will be
                        added to Etrigan object (`etrigan_add` list) so the other subsequent
                        ones can reuse them for further processing.
                        You only have to provide indexes of `etrigan_add` list,
                        (an int (example: 2) for single index or a string (example: '1:4') for slices)
                        as first returning element.

        `want_quit`
                :Default: `False`
                        If `True`, runs Etrigan `quit_on_start` or `quit_on_stop`
                        lists of your custom functions at the end of `start` or `stop` operations.
                        These can return elements as `funcs_to_daemonize`.

        `logfile`
                :Default: `None`
                        Path to the output log file.

        `loglevel`
                :Default: `None`
                        Set the log level of logging messages.

        `mute`
                :Default: `False`
                        Disable all stdout and stderr messages (before double forking).

        `pause_loop`
                :Default: `None`
                        Seconds of pause between the calling, in an infinite loop,
                        of every function in `funcs_to_daemonize` list.
                        If `-1`, no pause between the calling, in an infinite loop,
                        of every function in `funcs_to_daemonize` list.                   
                        If `None`, only one run (no infinite loop) of functions in
                        `funcs_to_daemonize` list, without pause.       
        """
        
        def __init__(self, pidfile,
                     stdin = os.devnull, stdout = os.devnull, stderr = os.devnull,
                     funcs_to_daemonize = [], want_quit = False,
                     logfile = None, loglevel = None,
                     mute = False, pause_loop = None):

                self.pidfile = pidfile                
                self.funcs_to_daemonize = funcs_to_daemonize
                self.stdin = stdin
                self.stdout = stdout
                self.stderr = stderr
                self.logfile = logfile
                self.loglevel = loglevel
                self.mute = mute
                self.want_quit = want_quit
                self.pause_loop = pause_loop
                # internal only.               
                self.homedir = '/'
                self.umask = 0o22
                self.etrigan_restart, self.etrigan_reload = (False for _ in range(2))
                self.etrigan_alive = True
                self.etrigan_add = []
                self.etrigan_index = None
                # seconds of pause between stop and start during the restart of the daemon.
                self.pause_restart = 5
                # when terminate a process, seconds to wait until kill the process with signal.
                # self.pause_kill = 3
                
                # create logfile.
                self.setup_files()

        def handle_terminate(self, signum, frame):
                if os.path.exists(self.pidfile):
                        self.etrigan_alive = False
                        # eventually run quit (on stop) function/s.
                        if self.want_quit:
                                if not isinstance(self.quit_on_stop, (list, tuple)):
                                        self.quit_on_stop = [self.quit_on_stop]
                                self.execute(self.quit_on_stop)
                        # then always run quit standard.
                        self.quit_standard()
                else:
                        self.view(self.logdaemon.error, self.emit_error, "Failed to stop the daemon process: can't find PIDFILE '%s'" %self.pidfile)
                sys.exit(0)

        def handle_reload(self, signum, frame):
                self.etrigan_reload = True

        def setup_files(self):
                self.pidfile = os.path.abspath(self.pidfile)
                
                if self.logfile is not None:                     
                        self.logdaemon = logging.getLogger('logdaemon')
                        self.logdaemon.setLevel(self.loglevel)
                        
                        filehandler = logging.FileHandler(self.logfile)
                        filehandler.setLevel(self.loglevel)
                        formatter = logging.Formatter(fmt = '[%(asctime)s] [%(levelname)8s] --- %(message)s',
                                                      datefmt = '%Y-%m-%d %H:%M:%S')
                        filehandler.setFormatter(formatter)
                        self.logdaemon.addHandler(filehandler)
                else:
                        nullhandler = logging.NullHandler()
                        self.logdaemon.addHandler(nullhandler)

        def emit_error(self, message, to_exit = True):
                """ Print an error message to STDERR. """
                if not self.mute:
                        sys.stderr.write(message + '\n')
                        sys.stderr.flush()
                if to_exit:
                        sys.exit(1)

        def emit_message(self, message, to_exit = False):
                """ Print a message to STDOUT. """
                if not self.mute:
                        sys.stdout.write(message + '\n')
                        sys.stdout.flush()
                if to_exit:
                        sys.exit(0)

        def view(self, logobj, emitobj, msg, **kwargs):
                options = {'to_exit' : False,
                           'silent' : False
                           }
                options.update(kwargs)

                if logobj:
                        logobj(msg)
                if emitobj:                        
                        if not options['silent']:
                                emitobj(msg, to_exit = options['to_exit'])

        def daemonize(self):
                """
                Double-forks the process to daemonize the script.
                see Stevens' "Advanced Programming in the UNIX Environment" for details (ISBN 0201563177)
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
                """
                self.view(self.logdaemon.debug, None, "Attempting to daemonize the process...")

                # First fork.
                self.fork(msg = "First fork")
                # Decouple from parent environment.
                self.detach()                
                # Second fork.
                self.fork(msg = "Second fork")
                # Write the PID file.
                self.create_pidfile()
                self.view(self.logdaemon.info, self.emit_message, "The daemon process has started.")
                # Redirect standard file descriptors.
                sys.stdout.flush()
                sys.stderr.flush()
                self.attach('stdin', mode = 'r')
                self.attach('stdout', mode = 'a+')

                try:
                        self.attach('stderr', mode = 'a+', buffering = 0)
                except ValueError:
                        # Python 3 can't have unbuffered text I/O.
                        self.attach('stderr', mode = 'a+', buffering = 1)

                # Handle signals.                
                signal.signal(signal.SIGINT, self.handle_terminate)
                signal.signal(signal.SIGTERM, self.handle_terminate) 
                signal.signal(signal.SIGHUP, self.handle_reload)
                #signal.signal(signal.SIGKILL....)

        def fork(self, msg):
                try:
                        pid = os.fork()
                        if pid > 0:                                
                                self.view(self.logdaemon.debug, None, msg + " success with PID %d." %pid)
                                # Exit from parent.
                                sys.exit(0)
                except Exception as e:
                        msg += " failed: %s." %str(e)
                        self.view(self.logdaemon.error, self.emit_error, msg)
                        
        def detach(self):
                # cd to root for a guarenteed working dir.
                try:
                        os.chdir(self.homedir)
                except Exception as e:
                        msg = "Unable to change working directory: %s." %str(e)
                        self.view(self.logdaemon.error, self.emit_error, msg)
                        
                # clear the session id to clear the controlling tty.
                pid = os.setsid()
                if pid == -1:
                        sys.exit(1)
                
                # set the umask so we have access to all files created by the daemon.
                try:
                        os.umask(self.umask)
                except Exception as e:
                        msg = "Unable to change file creation mask: %s." %str(e)
                        self.view(self.logdaemon.error, self.emit_error, msg)

        def attach(self, name, mode, buffering = -1):
                with open(getattr(self, name), mode, buffering) as stream:
                        os.dup2(stream.fileno(), getattr(sys, name).fileno())

        def checkfile(self, path, typearg, typefile):
                filename = os.path.basename(path)
                pathname = os.path.dirname(path)
                if not os.path.isdir(pathname):
                        msg = "argument %s: invalid directory: '%s'. Exiting..." %(typearg, pathname)
                        self.view(self.logdaemon.error, self.emit_error, msg)
                elif not filename.lower().endswith(typefile):
                        msg = "argument %s: not a %s file, invalid extension: '%s'. Exiting..." %(typearg, typefile, filename)
                        self.view(self.logdaemon.error, self.emit_error, msg)

        def create_pidfile(self):
                atexit.register(self.delete_pidfile)
                pid = os.getpid()
                try:
                        with open(self.pidfile, 'w+') as pf:
                             pf.write("%s\n" %pid)
                        self.view(self.logdaemon.debug, None, "PID %d written to '%s'." %(pid, self.pidfile))
                except Exception as e:
                        msg = "Unable to write PID to PIDFILE '%s': %s" %(self.pidfile, str(e))
                        self.view(self.logdaemon.error, self.emit_error, msg)

        def delete_pidfile(self, pid):
                # Remove the PID file.
                try:
                        os.remove(self.pidfile)
                        self.view(self.logdaemon.debug, None, "Removing PIDFILE '%s' with PID %d." %(self.pidfile, pid))
                except Exception as e:
                        if e.errno != errno.ENOENT:
                                self.view(self.logdaemon.error, self.emit_error, str(e))

        def get_pidfile(self):
                # Get the PID from the PID file.
                if self.pidfile is None:
                        return None
                if not os.path.isfile(self.pidfile):
                        return None

                try:
                        with open(self.pidfile, 'r') as pf:
                                pid = int(pf.read().strip())
                        self.view(self.logdaemon.debug, None, "Found PID %d in PIDFILE '%s'" %(pid, self.pidfile))
                except Exception as e:
                        self.view(self.logdaemon.warning, None, "Empty or broken PIDFILE")
                        pid = None

                def pid_exists(pid):
                        # psutil _psposix.py.
                        if pid == 0:
                                return True
                        try:
                                os.kill(pid, 0)
                        except OSError as e:
                                if e.errno == errno.ESRCH:
                                        return False
                                elif e.errno == errno.EPERM:
                                        return True
                                else:
                                        self.view(self.logdaemon.error, self.emit_error, str(e))
                        else:
                                return True

                if pid is not None and pid_exists(pid):
                        return pid
                else:
                        # Remove the stale PID file.
                        self.delete_pidfile(pid)
                        return None

        def start(self):
                """ Start the daemon. """
                self.view(self.logdaemon.info, self.emit_message, "Starting the daemon process...", silent = self.etrigan_restart)
                
                # Check for a PID file to see if the Daemon is already running.
                pid = self.get_pidfile()
                if pid is not None:
                        msg = "A previous daemon process with PIDFILE '%s' already exists. Daemon already running ?" %self.pidfile
                        self.view(self.logdaemon.warning, self.emit_error, msg, to_exit = False)
                        return

                # Daemonize the main process.
                self.daemonize()
                # Start a infinitive loop that periodically runs `funcs_to_daemonize`.
                self.loop()
                # eventualy run quit (on start) function/s.
                if self.want_quit:
                        if not isinstance(self.quit_on_start, (list, tuple)):
                                self.quit_on_start = [self.quit_on_start]
                        self.execute(self.quit_on_start)

        def stop(self):
                """ Stop the daemon. """
                self.view(None, self.emit_message, "Stopping the daemon process...", silent = self.etrigan_restart)
                
                self.logdaemon.disabled = True
                pid = self.get_pidfile()
                self.logdaemon.disabled = False
                if not pid:
                        # Just to be sure. A ValueError might occur
                        # if the PIDFILE is empty but does actually exist.
                        if os.path.exists(self.pidfile):
                                self.delete_pidfile(pid)

                        msg = "Can't find the daemon process with PIDFILE '%s'. Daemon not running ?" %self.pidfile
                        self.view(self.logdaemon.warning, self.emit_error, msg, to_exit = False)
                        return

                # Try to kill the daemon process.
                try:
                        while True:
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.1)
                except Exception as e:
                        if (e.errno != errno.ESRCH):
                                self.view(self.logdaemon.error, self.emit_error, "Failed to stop the daemon process: %s" %str(e))
                        else:
                                self.view(None, self.emit_message, "The daemon process has ended correctly.", silent = self.etrigan_restart)

        def restart(self):
                """ Restart the daemon. """
                self.view(self.logdaemon.info, self.emit_message, "Restarting the daemon process...")
                self.etrigan_restart = True
                self.stop()
                if self.pause_restart:
                        time.sleep(self.pause_restart)
                        self.etrigan_alive = True
                self.start()

        def reload(self):
                pass

        def status(self):
                """ Get status of the daemon. """
                self.view(self.logdaemon.info, self.emit_message, "Viewing the daemon process status...")

                if self.pidfile is None:
                        self.view(self.logdaemon.error, self.emit_error, "Cannot get the status of daemon without PIDFILE.")
           
                pid = self.get_pidfile()
                if pid is None:
                        self.view(self.logdaemon.info, self.emit_message, "The daemon process is not running.", to_exit = True)
                else:
                        try: 
                                with open("/proc/%d/status" %pid, 'r') as pf:
                                        pass
                                self.view(self.logdaemon.info, self.emit_message, "The daemon process is running.", to_exit = True)
                        except Exception as e:
                                msg = "There is not a process with the PIDFILE '%s': %s" %(self.pidfile, str(e))
                                self.view(self.logdaemon.error, self.emit_error, msg)

        def flatten(self, alistoflists, ltypes = Sequence):
                # https://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists/2158532#2158532
                alistoflists = list(alistoflists)
                while alistoflists:
                        while alistoflists and isinstance(alistoflists[0], ltypes):
                                alistoflists[0:1] = alistoflists[0]
                        if alistoflists: yield alistoflists.pop(0)

        def exclude(self, func):
                from inspect import getargspec
                args = getargspec(func)
                if callable(func):
                        try:
                                args[0].pop(0)
                        except IndexError:
                                pass
                        return args
                else:
                        self.view(self.logdaemon.error, self.emit_error, "Not a function.")
                        return

        def execute(self, some_functions):
                returned = None
                if isinstance(some_functions, (list, tuple)):
                        for func in some_functions: 
                                l_req = len(self.exclude(func)[0])
                                
                                if l_req == 0:
                                        returned = func()
                                else:
                                        l_add = len(self.etrigan_add)
                                        if l_req > l_add:
                                                self.view(self.logdaemon.error, self.emit_error,
                                                          "Can't evaluate function: given %s, required %s." %(l_add, l_req))
                                                return
                                        else:
                                                arguments = self.etrigan_add[self.etrigan_index]
                                                l_args = (len(arguments) if isinstance(arguments, list) else 1)
                                                if (l_args > l_req) or (l_args < l_req):
                                                        self.view(self.logdaemon.error, self.emit_error,
                                                                  "Can't evaluate function: given %s, required %s." %(l_args, l_req))
                                                        return
                                                else:
                                                        if isinstance(arguments, list):
                                                                returned = func(*arguments)
                                                        else:
                                                                returned = func(arguments)

                                if returned:
                                        if isinstance(returned, (list, tuple)):
                                                if isinstance(returned[0], int):
                                                        self.etrigan_index = returned[0]
                                                else:
                                                        self.etrigan_index = slice(*map(int, returned[0].split(':')))
                                                if returned[1:] != []:
                                                        self.etrigan_add.append(returned[1:])
                                                        self.etrigan_add = list(self.flatten(self.etrigan_add))
                                        else:
                                                self.view(self.logdaemon.error, self.emit_error, "Function should return list or tuple.")
                                        returned = None
                else:
                        if some_functions is None:
                                self.run()

        def loop(self):
                try:
                        if self.pause_loop is None:
                                # one-shot.
                                self.execute(self.funcs_to_daemonize)
                        else:
                                if self.pause_loop >= 0:
                                        # infinite with pause.
                                        time.sleep(self.pause_loop)
                                        while self.etrigan_alive:
                                                self.execute(self.funcs_to_daemonize)
                                                time.sleep(self.pause_loop)
                                elif self.pause_loop == -1:
                                        # infinite without pause.
                                        while self.etrigan_alive:
                                                self.execute(self.funcs_to_daemonize)
                except Exception as e:
                        msg = "The daemon process start method failed: %s" %str(e)
                        self.view(self.logdaemon.error, self.emit_error, msg)
                        
        def quit_standard(self):
                self.view(self.logdaemon.info, None, "Stopping the daemon process...")
                self.delete_pidfile(self.get_pidfile())
                self.view(self.logdaemon.info, None, "The daemon process has ended correctly.")

        def quit_on_start(self):
                """
                Override this method when you subclass Daemon.
                """
                self.quit_standard()
                
        def quit_on_stop(self):
                """
                Override this method when you subclass Daemon.
                """
                pass

        def run(self):
                """
                Override this method when you subclass Daemon.
                It will be called after the process has been
                daemonized by start() or restart().
                """
                pass
                
#-----------------------------------------------------------------------------------------------------------------------------------------------------------

class JasonBlood(Etrigan):
        def run(self):
                jasonblood_func()

def jasonblood_func():  
        with open(os.path.join('.', 'etrigan_test.txt'), 'a') as file:
                file.write("Yarva Demonicus Etrigan " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + '\n')

def Etrigan_parser(parser = None):
        if parser is None:
                # create a new parser.
                parser = argparse.ArgumentParser(description = __description__, epilog = __version__)
        if not parser.add_help:
                # create help argument.
                parser.add_argument("-h", "--help", action = "help", help = "show this help message and exit")
        
        # attach to an existent parser.
        parser.add_argument("operation", action = "store", choices = ["start", "stop", "restart", "status", "reload"],
                            help = "Select an operation for daemon.", type = str)
        parser.add_argument("--etrigan-pid",
                            action = "store", dest = "etriganpid", default = "/tmp/etrigan.pid",
                            help = "Choose a pidfile path. Default is \"/tmp/etrigan.pid\".", type = str) #'/var/run/etrigan.pid'
        parser.add_argument("--etrigan-log",
                            action = "store", dest = "etriganlog", default = os.path.join('.', "etrigan.log"),
                            help = "Use this option to choose an output log file; for not logging don't select it. Default is \"etrigan.log\".", type = str)
        parser.add_argument("--etrigan-lev",
                            action = "store", dest = "etriganlev", default = "DEBUG",
                            choices = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                            help = "Use this option to set a log level. Default is \"DEBUG\".", type = str)
        parser.add_argument("--etrigan-mute",
                            action = "store_const", dest = 'etriganmute', const = True, default = False,
                            help = "Disable all stdout and stderr messages.")
        return parser

class Etrigan_check(object):
        def emit_opt_err(self, msg):
                print(msg)
                sys.exit(1)

        def checkfile(self, path, typearg, typefile):
                filename, extension = os.path.splitext(path)
                pathname = os.path.dirname(path)
                if not os.path.isdir(pathname):
                        msg = "argument `%s`: invalid directory: '%s'. Exiting..." %(typearg, pathname)
                        self.emit_opt_err(msg)
                elif not extension == typefile:
                        msg = "argument `%s`: not a %s file, invalid extension: '%s'. Exiting..." %(typearg, typefile, extension)
                        self.emit_opt_err(msg)

        def checkfunction(self, funcs, booleans):
                if not isinstance(funcs, (list, tuple)):
                        if funcs is not None:
                                msg = "argument `funcs_to_daemonize`: provide list, tuple or None"
                                self.emit_opt_err(msg)
                                        
                for elem in booleans:
                        if not type(elem) == bool:
                                msg = "argument `want_quit`: not a boolean."
                                self.emit_opt_err(msg)
        
def Etrigan_job(type_oper, daemon_obj):
        Etrigan_check().checkfunction(daemon_obj.funcs_to_daemonize,
                                      [daemon_obj.want_quit])
        if type_oper == "start":
                daemon_obj.start()
        elif type_oper == "stop":
                daemon_obj.stop()
        elif type_oper == "restart":
                daemon_obj.restart()
        elif type_oper == "status":
                daemon_obj.status()
        elif type_oper == "reload":
                daemon_obj.reload()
        sys.exit(0)

def main():
        # Parse arguments.
        parser = Etrigan_parser()
        args = vars(parser.parse_args())
        # Check arguments.
        Etrigan_check().checkfile(args['etriganpid'], '--etrigan-pid', '.pid')
        Etrigan_check().checkfile(args['etriganlog'], '--etrigan-log', '.log')

        # Setup daemon.
        jasonblood_1 = Etrigan(pidfile = args['etriganpid'], logfile = args['etriganlog'], loglevel = args['etriganlev'],
                               mute = args['etriganmute'],
                               funcs_to_daemonize = [jasonblood_func], pause_loop = 5)

##        jasonblood_2 = JasonBlood(pidfile = args['etriganpid'], logfile = args['etriganlog'], loglevel = args['etriganlev'],
##                                  mute = args['etriganmute'],
##                                  funcs_to_daemonize = None, pause_loop = 5)
        # Do job.
        Etrigan_job(args['operation'], jasonblood_1)
        
if __name__ == '__main__':
        main()
