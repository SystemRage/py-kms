#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
from time import sleep
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import tkinter.font as tkFont

from pykms_Server import srv_options, srv_version, srv_config, server_terminate, serverqueue, serverthread
from pykms_GuiMisc import ToolTip, TextDoubleScroll, TextRedirect, ListboxOfRadiobuttons
from pykms_GuiMisc import custom_background, custom_pages
from pykms_Client import clt_options, clt_version, clt_config, client_thread

gui_version             = "py-kms_gui_v3.0"
__license__             = "MIT License"
__author__              = u"Matteo ℱan <SystemRage@protonmail.com>"
__copyright__           = "© Copyright 2020"
__url__                 = "https://github.com/SystemRage/py-kms"
gui_description         = "A GUI for py-kms."

##---------------------------------------------------------------------------------------------------------------------------------------------------------
def get_ip_address():
        if os.name == 'posix':
                import subprocess
                ip = subprocess.getoutput("hostname -I")
        elif os.name == 'nt':
                import socket
                ip = socket.gethostbyname(socket.gethostname())
        else:
                ip = 'Unknown'
        return ip

def gui_redirector(stream, redirect_to = TextRedirect.Pretty, redirect_conditio = True, stderr_side = "srv"):
        global txsrv, txclt, txcol
        if redirect_conditio:
                if stream == 'stdout':
                        sys.stdout = redirect_to(txsrv, txclt, txcol)
                elif stream == 'stderr':
                        sys.stderr = redirect_to(txsrv, txclt, txcol, stderr_side)
                else:
                        stream = redirect_to(txsrv, txclt, txcol)
                        return stream

def gui_redirector_setup():
        TextRedirect.Pretty.tag_num = 0
        TextRedirect.Pretty.newlinecut = [-1, -2, -4, -5]

def gui_redirector_clear():
        global txsrv, oysrv
        try:
                if oysrv:
                        txsrv.configure(state = 'normal')
                        txsrv.delete('1.0', 'end')
                        txsrv.configure(state = 'disabled')
        except:
                # self.onlysrv not defined (menu not used)
                pass

##-----------------------------------------------------------------------------------------------------------------------------------------------------------

class KmsGui(tk.Tk):
        def __init__(self, *args, **kwargs):
                tk.Tk.__init__(self, *args, **kwargs)
                self.wraplength = 200
                serverthread.with_gui = True
                self.validation_int = (self.register(self.validate_int), "%S")
                self.validation_float = (self.register(self.validate_float), "%P")

                ## Define fonts and colors.
                self.customfonts = {'btn' : tkFont.Font(family = 'Fixedsys', size = 11, weight = 'bold'),
                                    'oth' : tkFont.Font(family = 'Times', size = 9, weight = 'bold'),
                                    'opt' : tkFont.Font(family = 'Fixedsys', size = 9, weight = 'bold'),
                                    'lst' : tkFont.Font(family = 'Fixedsys', size = 8, weight = 'bold', slant = 'italic'),
                                    'msg' : tkFont.Font(family = 'Monospace', size = 6), # need a monospaced type (like courier, etc..).
                                    }

                self.customcolors = { 'black'   : '#000000',
                                      'white'   : '#FFFFFF',
                                      'green'   : '#00EE76',
                                      'yellow'  : '#FFFF00',
                                      'magenta' : '#CD00CD',
                                      'orange'  : '#FFA500',
                                      'red'     : '#FF4500',
                                      'blue'    : '#1E90FF',
                                      'cyan'    : '#AFEEEE',
                                      'lavender': '#E6E6FA',
                                      'brown'   : '#A52A2A',
                                      }

                self.option_add('*TCombobox*Listbox.font', self.customfonts['lst'])

                self.gui_create()

        def invert(self, widgets = []):
                for widget in widgets:
                        if widget['state'] == 'normal':
                                widget.configure(state = 'disabled')
                        elif widget['state'] == 'disabled':
                                widget.configure(state = 'normal')

        def gui_menu(self):
                self.onlysrv, self.onlyclt = (False for _ in range(2))
                menubar = tk.Menu(self)
                prefmenu = tk.Menu(menubar, tearoff = 0, font = ("Noto Sans Regular", 10), borderwidth = 3, relief = 'ridge')
                menubar.add_cascade(label = 'Preferences', menu = prefmenu)
                prefmenu.add_command(label = 'Enable server-side mode', command = lambda: self.pref_onlysrv(prefmenu))
                prefmenu.add_command(label = 'Enable client-side mode', command = lambda: self.pref_onlyclt(prefmenu))
                self.config(menu = menubar)
                
        def pref_onlysrv(self, menu):
                global oysrv

                if self.onlyclt or serverthread.is_running_server:
                        return
                self.onlysrv = not self.onlysrv
                if self.onlysrv:
                        menu.entryconfigure(0, label = 'Disable server-side mode')
                        self.clt_on_show(force_remove = True)
                else:
                        menu.entryconfigure(0, label = 'Enable server-side mode')
                self.invert(widgets = [self.shbtnclt])
                oysrv = self.onlysrv

        def pref_onlyclt(self, menu):
                if self.onlysrv or serverthread.is_running_server:
                        return
                self.onlyclt = not self.onlyclt
                if self.onlyclt:
                        menu.entryconfigure(1, label = 'Disable client-side mode')
                        if self.shbtnclt['text'] == 'SHOW\nCLIENT':
                                self.clt_on_show(force_view = True)
                        self.optsrvwin.grid_remove()
                        self.msgsrvwin.grid_remove()
                        gui_redirector('stderr', redirect_to = TextRedirect.Stderr, stderr_side = "clt")
                else:
                        menu.entryconfigure(1, label = 'Enable client-side mode')
                        self.optsrvwin.grid()
                        self.msgsrvwin.grid()
                        gui_redirector('stderr', redirect_to = TextRedirect.Stderr)

                self.invert(widgets = [self.runbtnsrv, self.shbtnclt, self.runbtnclt])

        def gui_create(self):
                ## Create server gui
                self.gui_srv()
                ## Create client gui + other operations.
                self.gui_complete()
                ## Create menu.
                self.gui_menu()
                ## Create globals for printing process (redirect stdout).
                global txsrv, txclt, txcol
                txsrv = self.textboxsrv.get()
                txclt = self.textboxclt.get()
                txcol = self.customcolors
                ## Redirect stderr.
                gui_redirector('stderr', redirect_to = TextRedirect.Stderr)

        def gui_pages_show(self, pagename, side):
                # https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
                # https://www.reddit.com/r/learnpython/comments/7xxtsy/trying_to_understand_tkinter_and_how_to_switch/
                pageside = self.pagewidgets[side]
                tk.Misc.lift(pageside["PageWin"][pagename], aboveThis = None)
                keylist = list(pageside["PageWin"].keys())

                for elem in [pageside["BtnAni"], pageside["LblAni"]]:
                        if pagename == "PageStart":
                                elem["Left"].config(state = "disabled")
                                if len(keylist) == 2:
                                        elem["Right"].config(state = "normal")
                        elif pagename == "PageEnd":
                                elem["Right"].config(state = "disabled")
                                if len(keylist) == 2:
                                        elem["Left"].config(state = "normal")
                        else:
                                for where in ["Left", "Right"]:
                                        elem[where].config(state = "normal")

                if pagename != "PageStart":
                        page_l = keylist[keylist.index(pagename) - 1]
                        pageside["BtnAni"]["Left"]['command'] = lambda pag=page_l, pos=side: self.gui_pages_show(pag, pos)
                if pagename != "PageEnd":
                        page_r = keylist[keylist.index(pagename) + 1]
                        pageside["BtnAni"]["Right"]['command'] = lambda pag=page_r, pos=side: self.gui_pages_show(pag, pos)

        def gui_pages_buttons(self, parent, side):
                btnwin = tk.Canvas(parent, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                btnwin.grid(row = 14, column = 2, padx = 2, pady = 2, sticky = 'nsew')
                btnwin.grid_columnconfigure(1, weight = 1)
                self.pagewidgets[side]["BtnWin"] = btnwin

                for position in ["Left", "Right"]:
                        if position == "Left":
                                col = [0, 0, 1]
                                stick = 'e'
                        elif position == "Right":
                                col = [2, 1, 0]
                                stick = 'w'

                        aniwin = tk.Canvas(btnwin, background = self.customcolors['white'], borderwidth = 0, relief = 'ridge')
                        aniwin.grid(row = 0, column = col[0], padx = 5, pady = 5, sticky = 'nsew')
                        self.pagewidgets[side]["AniWin"][position] = aniwin

                        lblani = tk.Label(aniwin, width = 1, height = 1)
                        lblani.grid(row = 0, column = col[1], padx = 2, pady = 2, sticky = stick)
                        self.pagewidgets[side]["LblAni"][position] = lblani

                        btnani = tk.Button(aniwin)
                        btnani.grid(row = 0, column = col[2], padx = 2, pady = 2, sticky = stick)
                        self.pagewidgets[side]["BtnAni"][position] = btnani
                ## Customize buttons.
                custom_pages(self, side)

        def gui_pages_create(self, parent, side, create = {}):
                self.pagewidgets.update({side : {"PageWin" : create,
                                                 "BtnWin"  : None,
                                                 "BtnAni"  :  {"Left"  : None,
                                                               "Right" : None},
                                                 "AniWin"  :  {"Left"  : None,
                                                               "Right" : None},
                                                 "LblAni"  :  {"Left"  : None,
                                                               "Right" : None},
                                                 }
                                         })

                for pagename in self.pagewidgets[side]["PageWin"].keys():
                        page = tk.Canvas(parent, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                        self.pagewidgets[side]["PageWin"][pagename] = page
                        page.grid(row = 0, column = 2, padx = 2, pady = 2, sticky = "nsew")
                        page.grid_columnconfigure(1, weight = 1)
                self.gui_pages_buttons(parent = parent, side = side)
                self.gui_pages_show("PageStart", side = side)

        def gui_store(self, side, typewidgets):
                stored = []
                for pagename in self.pagewidgets[side]["PageWin"].keys():
                        for widget in self.pagewidgets[side]["PageWin"][pagename].winfo_children():
                                if widget.winfo_class() in typewidgets:
                                        stored.append(widget)
                return stored

        def gui_srv(self):
                ## Create main containers. ------------------------------------------------------------------------------------------------------------------
                self.masterwin = tk.Canvas(self, borderwidth = 3, relief = tk.RIDGE)
                self.btnsrvwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.optsrvwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.msgsrvwin = tk.Frame(self.masterwin, background = self.customcolors['black'], relief = 'ridge', width = 300, height = 200)

                ## Layout main containers.
                self.masterwin.grid(row = 0, column = 0, sticky = 'nsew')
                self.btnsrvwin.grid(row = 0, column = 1, padx = 2, pady = 2, sticky = 'nw')
                self.optsrvwin.grid(row = 0, column = 2, padx = 2, pady = 2, sticky = 'nsew')
                self.optsrvwin.grid_rowconfigure(0, weight = 1)
                self.optsrvwin.grid_columnconfigure(1, weight = 1)

                self.pagewidgets = {}

                ## Subpages of "optsrvwin".
                self.gui_pages_create(parent = self.optsrvwin, side = "Srv", create = {"PageStart": None,
                                                                                       "PageEnd": None})

                ## Continue to grid.
                self.msgsrvwin.grid(row = 1, column = 2, padx = 1, pady = 1, sticky = 'nsew')
                self.msgsrvwin.grid_propagate(False)
                self.msgsrvwin.grid_columnconfigure(0, weight = 1)
                self.msgsrvwin.grid_rowconfigure(0, weight = 1)

                ## Create widgets (btnsrvwin) ---------------------------------------------------------------------------------------------------------------
                self.statesrv = tk.Label(self.btnsrvwin, text = 'Server\nState:\nStopped', font = self.customfonts['oth'],
                                         foreground = self.customcolors['red'])
                self.runbtnsrv = tk.Button(self.btnsrvwin, text = 'START\nSERVER', background = self.customcolors['green'],
                                           foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                           command = self.srv_on_start)
                self.shbtnclt = tk.Button(self.btnsrvwin, text = 'SHOW\nCLIENT', background = self.customcolors['magenta'],
                                          foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                          command = self.clt_on_show)
                self.defaubtnsrv = tk.Button(self.btnsrvwin, text = 'DEFAULTS', background = self.customcolors['brown'],
                                             foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                             command = self.on_defaults)
                self.clearbtnsrv = tk.Button(self.btnsrvwin, text = 'CLEAR', background = self.customcolors['orange'],
                                             foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                             command = lambda: self.on_clear([txsrv, txclt]))
                self.exitbtnsrv = tk.Button(self.btnsrvwin, text = 'EXIT', background = self.customcolors['black'],
                                            foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                            command = self.on_exit)

                ## Layout widgets (btnsrvwin)
                self.statesrv.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.runbtnsrv.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.shbtnclt.grid(row = 2, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.defaubtnsrv.grid(row = 3, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.clearbtnsrv.grid(row = 4, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.exitbtnsrv.grid(row = 5, column = 0, padx = 2, pady = 2, sticky = 'ew')

                ## Create widgets (optsrvwin:Srv:PageWin:PageStart) -----------------------------------------------------------------------------------------
                # Version.
                ver = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"],
                               text = 'You are running server version: ' + srv_version, font = self.customfonts['oth'],
                               foreground = self.customcolors['red'])
                # Ip Address.
                srvipaddlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'IP Address: ', font = self.customfonts['opt'])
                self.srvipadd = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'ip')
                self.srvipadd.insert('end', srv_options['ip']['def'])
                ToolTip(self.srvipadd, text = srv_options['ip']['help'], wraplength = self.wraplength)
                myipadd = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Your IP address is: {}'.format(get_ip_address()),
                                   font = self.customfonts['oth'], foreground = self.customcolors['red'])
                # Port.
                srvportlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Port: ', font = self.customfonts['opt'])
                self.srvport = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'port',
                                        validate = "key", validatecommand = self.validation_int)
                self.srvport.insert('end', str(srv_options['port']['def']))
                ToolTip(self.srvport, text = srv_options['port']['help'], wraplength = self.wraplength)
                # EPID.
                epidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'EPID: ', font = self.customfonts['opt'])
                self.epid = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'epid')
                self.epid.insert('end', str(srv_options['epid']['def']))
                ToolTip(self.epid, text = srv_options['epid']['help'], wraplength = self.wraplength)
                # LCID.
                lcidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'LCID: ', font = self.customfonts['opt'])
                self.lcid = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'lcid',
                                     validate = "key", validatecommand = self.validation_int)
                self.lcid.insert('end', str(srv_options['lcid']['def']))
                ToolTip(self.lcid, text = srv_options['lcid']['help'], wraplength = self.wraplength)
                # HWID.
                hwidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'HWID: ', font = self.customfonts['opt'])
                self.hwid = ttk.Combobox(self.pagewidgets["Srv"]["PageWin"]["PageStart"], values = (str(srv_options['hwid']['def']), 'RANDOM'),
                                         width = 17, height = 10, font = self.customfonts['lst'], name = 'hwid')
                self.hwid.set(str(srv_options['hwid']['def']))
                ToolTip(self.hwid, text = srv_options['hwid']['help'], wraplength = self.wraplength)
                # Client Count
                countlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Client Count: ', font = self.customfonts['opt'])
                self.count = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'count')
                self.count.insert('end', str(srv_options['count']['def']))
                ToolTip(self.count, text = srv_options['count']['help'], wraplength = self.wraplength)
                # Activation Interval.
                activlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Activation Interval: ', font = self.customfonts['opt'])
                self.activ = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'activation',
                                      validate = "key", validatecommand = self.validation_int)
                self.activ.insert('end', str(srv_options['activation']['def']))
                ToolTip(self.activ, text = srv_options['activation']['help'], wraplength = self.wraplength)
                # Renewal Interval.
                renewlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Renewal Interval: ', font = self.customfonts['opt'])
                self.renew = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'renewal',
                                      validate = "key", validatecommand = self.validation_int)
                self.renew.insert('end', str(srv_options['renewal']['def']))
                ToolTip(self.renew, text = srv_options['renewal']['help'], wraplength = self.wraplength)
                # Logfile.
                srvfilelbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Logfile Path / Name: ', font = self.customfonts['opt'])
                self.srvfile = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'lfile')
                self.srvfile.insert('end', srv_options['lfile']['def'])
                self.srvfile.xview_moveto(1)
                ToolTip(self.srvfile, text = srv_options['lfile']['help'], wraplength = self.wraplength)
                srvfilebtnwin = tk.Button(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Browse', font = self.customfonts['opt'],
                                          command = lambda: self.on_browse(self.srvfile, srv_options))
                # Loglevel.
                srvlevellbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Loglevel: ', font = self.customfonts['opt'])
                self.srvlevel = ttk.Combobox(self.pagewidgets["Srv"]["PageWin"]["PageStart"], values = tuple(srv_options['llevel']['choi']),
                                             width = 10, height = 10, font = self.customfonts['lst'], state = "readonly", name = 'llevel')
                self.srvlevel.set(srv_options['llevel']['def'])
                ToolTip(self.srvlevel, text = srv_options['llevel']['help'], wraplength = self.wraplength)
                # Logsize.
                srvsizelbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Logsize: ', font = self.customfonts['opt'])
                self.srvsize = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'lsize',
                                        validate = "key", validatecommand = self.validation_float)
                self.srvsize.insert('end', srv_options['lsize']['def'])
                ToolTip(self.srvsize, text = srv_options['lsize']['help'], wraplength = self.wraplength)
                # Asynchronous messages.
                self.chkvalsrvasy = tk.BooleanVar()
                self.chkvalsrvasy.set(srv_options['asyncmsg']['def'])
                chksrvasy = tk.Checkbutton(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Async\nMsg',
                                           font = self.customfonts['opt'], var = self.chkvalsrvasy, relief = 'groove', name = 'asyncmsg')
                ToolTip(chksrvasy, text = srv_options['asyncmsg']['help'], wraplength = self.wraplength)

                # Listbox radiobuttons server.
                self.chksrvfile = ListboxOfRadiobuttons(self.pagewidgets["Srv"]["PageWin"]["PageStart"],
                                                        ['FILE', 'FILEOFF', 'STDOUT', 'STDOUTOFF', 'FILESTDOUT'],
                                                        self.customfonts['lst'],
                                                        changed = [(self.srvfile, srv_options['lfile']['def']),
                                                                   (srvfilebtnwin, ''),
                                                                   (self.srvsize, srv_options['lsize']['def']),
                                                                   (self.srvlevel, srv_options['llevel']['def'])],
                                                        width = 10, height = 1, borderwidth = 2, relief = 'ridge')

                ## Layout widgets (optsrvwin:Srv:PageWin:PageStart)
                ver.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = 'ew')
                srvipaddlbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvipadd.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'ew')
                myipadd.grid(row = 2, column = 1, columnspan = 2, padx = 5, pady = 5, sticky = 'ew')
                srvportlbl.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvport.grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'ew')
                epidlbl.grid(row = 4, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.epid.grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'ew')
                lcidlbl.grid(row = 5, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.lcid.grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'ew')
                hwidlbl.grid(row = 6, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.hwid.grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'ew')
                countlbl.grid(row = 7, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.count.grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'ew')
                activlbl.grid(row = 8, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.activ.grid(row = 8, column = 1, padx = 5, pady = 5, sticky = 'ew')
                renewlbl.grid(row = 9, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.renew.grid(row = 9, column = 1, padx = 5, pady = 5, sticky = 'ew')
                srvfilelbl.grid(row = 10, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvfile.grid(row = 10, column = 1, padx = 5, pady = 5, sticky = 'ew')
                srvfilebtnwin.grid(row = 10, column = 2, padx = 5, pady = 5, sticky = 'ew')
                self.chksrvfile.grid(row = 11, column = 1, padx = 5, pady = 5, sticky = 'ew')
                chksrvasy.grid(row = 11, column = 2, padx = 5, pady = 5, sticky = 'ew')
                srvlevellbl.grid(row = 12, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvlevel.grid(row = 12, column = 1, padx = 5, pady = 5, sticky = 'ew')
                srvsizelbl.grid(row = 13, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvsize.grid(row = 13, column = 1, padx = 5, pady = 5, sticky = 'ew')

                ## Create widgets (optsrvwin:Srv:PageWin:PageEnd)-------------------------------------------------------------------------------------------
                # Timeout connection.
                srvtimeout0lbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], text = 'Timeout connection: ', font = self.customfonts['opt'])
                self.srvtimeout0 = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 16, font = self.customfonts['opt'], name = 'time0')
                self.srvtimeout0.insert('end', str(srv_options['time0']['def']))
                ToolTip(self.srvtimeout0, text = srv_options['time0']['help'], wraplength = self.wraplength)
                # Timeout send/recv.
                srvtimeout1lbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], text = 'Timeout send-recv: ', font = self.customfonts['opt'])
                self.srvtimeout1 = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 16, font = self.customfonts['opt'], name = 'time1')
                self.srvtimeout1.insert('end', str(srv_options['time1']['def']))
                ToolTip(self.srvtimeout1, text = srv_options['time1']['help'], wraplength = self.wraplength)
                # Sqlite database.
                self.chkvalsql = tk.BooleanVar()
                self.chkvalsql.set(srv_options['sql']['def'])
                self.chkfilesql = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 16, font = self.customfonts['opt'], name = 'sql')
                self.chkfilesql.insert('end', srv_options['sql']['file'])
                self.chkfilesql.xview_moveto(1)
                self.chkfilesql.configure(state = 'disabled')

                chksql = tk.Checkbutton(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], text = 'Create Sqlite\nDatabase',
                                        font = self.customfonts['opt'], var = self.chkvalsql, relief = 'groove',
                                        command = lambda: self.sql_status())
                ToolTip(chksql, text = srv_options['sql']['help'], wraplength = self.wraplength)

                ## Layout widgets (optsrvwin:Srv:PageWin:PageEnd)
                # a label for vertical aligning with PageStart
                tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 0,
                         height = 0, bg = self.customcolors['lavender']).grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nw')
                srvtimeout0lbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvtimeout0.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'w')
                srvtimeout1lbl.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvtimeout1.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'w')
                chksql.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.chkfilesql.grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')

                # Store server-side widgets.
                self.storewidgets_srv = self.gui_store(side = "Srv", typewidgets = ['Button', 'Entry', 'TCombobox', 'Checkbutton'])
                self.storewidgets_srv.append(self.chksrvfile)

                ## Create widgets and layout (msgsrvwin) ---------------------------------------------------------------------------------------------------
                self.textboxsrv = TextDoubleScroll(self.msgsrvwin, background = self.customcolors['black'], wrap = 'none', state = 'disabled',
                                                   relief = 'ridge', font = self.customfonts['msg'])
                self.textboxsrv.put()

        def sql_status(self):
                if self.chkvalsql.get():
                        self.chkfilesql.configure(state = 'normal')
                else:
                        self.chkfilesql.insert('end', srv_options['sql']['file'])
                        self.chkfilesql.xview_moveto(1)
                        self.chkfilesql.configure(state = 'disabled')

        def always_centered(self, geo, centered, refs):
                x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
                y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
                w, h, dx, dy = geo.split('+')[0].split('x') + geo.split('+')[1:]

                if w == refs[1]:
                        if centered:
                                self.geometry('+%d+%d' %(x, y))
                                centered = False
                elif w == refs[0]:
                        if not centered:
                                self.geometry('+%d+%d' %(x, y))
                                centered = True

                if dx != str(x) or dy != str(y):
                        self.geometry('+%d+%d' %(x, 0))

                self.after(200, self.always_centered, self.geometry(), centered, refs)

        def gui_complete(self):
                ## Create client widgets (optcltwin, msgcltwin, btncltwin)
                self.update_idletasks()   # update Gui to get btnsrvwin values --> btncltwin.
                minw, minh = self.winfo_width(), self.winfo_height()
                self.iconify()  
                self.gui_clt()
                maxw, minh = self.winfo_width(), self.winfo_height()
                ## Main window custom background.
                self.update_idletasks()   # update Gui for custom background
                self.iconify()
                custom_background(self)
                ## Main window other modifications.
                self.eval('tk::PlaceWindow %s center' %self.winfo_pathname(self.winfo_id()))
                self.wm_attributes("-topmost", True)
                self.protocol("WM_DELETE_WINDOW", lambda: 0)
                ## Disable maximize button.
                self.resizable(False, False)
                ## Centered window.
                self.always_centered(self.geometry(), False, [minw, maxw])

        def get_position(self, widget):
                x, y = (widget.winfo_x(), widget.winfo_y())
                w, h = (widget.winfo_width(), widget.winfo_height())
                return x, y, w, h
                
        def gui_clt(self):
                self.count_clear, self.keep_clear = (0, '0.0')
                self.optcltwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.msgcltwin = tk.Frame(self.masterwin, background = self.customcolors['black'], relief = 'ridge', width = 300, height = 200)
                self.btncltwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')

                xb, yb, wb, hb = self.get_position(self.btnsrvwin)
                self.btncltwin_X = xb
                self.btncltwin_Y = yb + hb + 6
                self.btncltwin.place(x = self.btncltwin_X, y = self.btncltwin_Y, bordermode = 'outside', anchor = 'center')

                self.optcltwin.grid(row = 0, column = 4, padx = 2, pady = 2, sticky = 'nsew')
                self.optcltwin.grid_rowconfigure(0, weight = 1)
                self.optcltwin.grid_columnconfigure(1, weight = 1)

                ## Subpages of "optcltwin".
                self.gui_pages_create(parent = self.optcltwin, side = "Clt", create = {"PageStart": None,
                                                                                       "PageEnd": None})

                ## Continue to grid.
                self.msgcltwin.grid(row = 1, column = 4, padx = 1, pady = 1, sticky = 'nsew')
                self.msgcltwin.grid_propagate(False)
                self.msgcltwin.grid_columnconfigure(0, weight = 1)
                self.msgcltwin.grid_rowconfigure(0, weight = 1)

                ## Create widgets (btncltwin) ----------------------------------------------------------------------------------------------------------------
                self.runbtnclt = tk.Button(self.btncltwin, text = 'START\nCLIENT', background = self.customcolors['blue'],
                                           foreground = self.customcolors['white'], relief = 'raised', font = self.customfonts['btn'],
                                           state = 'disabled', command = self.clt_on_start, width = 8, height = 2)

                ## Layout widgets (btncltwin)
                self.runbtnclt.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
                
                ## Create widgets (optcltwin:Clt:PageWin:PageStart) ------------------------------------------------------------------------------------------
                # Version.
                cltver = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'You are running client version: ' + clt_version,
                                  font = self.customfonts['oth'], foreground = self.customcolors['red'])
                # Ip Address.
                cltipaddlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'IP Address: ', font = self.customfonts['opt'])
                self.cltipadd = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'ip')
                self.cltipadd.insert('end', clt_options['ip']['def'])
                ToolTip(self.cltipadd, text = clt_options['ip']['help'], wraplength = self.wraplength)
                # Port.
                cltportlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Port: ', font = self.customfonts['opt'])
                self.cltport = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'port',
                                        validate = "key", validatecommand = self.validation_int)
                self.cltport.insert('end', str(clt_options['port']['def']))
                ToolTip(self.cltport, text = clt_options['port']['help'], wraplength = self.wraplength)
                # Mode.
                cltmodelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Mode: ', font = self.customfonts['opt'])
                self.cltmode = ttk.Combobox(self.pagewidgets["Clt"]["PageWin"]["PageStart"], values = tuple(clt_options['mode']['choi']),
                                            width = 17, height = 10, font = self.customfonts['lst'], state = "readonly", name = 'mode')
                self.cltmode.set(clt_options['mode']['def'])
                ToolTip(self.cltmode, text = clt_options['mode']['help'], wraplength = self.wraplength)
                # CMID.
                cltcmidlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'CMID: ', font = self.customfonts['opt'])
                self.cltcmid = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'cmid')
                self.cltcmid.insert('end', str(clt_options['cmid']['def']))
                ToolTip(self.cltcmid, text = clt_options['cmid']['help'], wraplength = self.wraplength)
                # Machine Name.
                cltnamelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Machine Name: ', font = self.customfonts['opt'])
                self.cltname = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'name')
                self.cltname.insert('end', str(clt_options['name']['def']))
                ToolTip(self.cltname, text = clt_options['name']['help'], wraplength = self.wraplength)
                # Logfile.
                cltfilelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Logfile Path / Name: ', font = self.customfonts['opt'])
                self.cltfile = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'lfile')
                self.cltfile.insert('end', clt_options['lfile']['def'])
                self.cltfile.xview_moveto(1)
                ToolTip(self.cltfile, text = clt_options['lfile']['help'], wraplength = self.wraplength)
                cltfilebtnwin = tk.Button(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Browse', font = self.customfonts['opt'],
                                          command = lambda: self.on_browse(self.cltfile, clt_options))
                # Loglevel.
                cltlevellbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Loglevel: ', font = self.customfonts['opt'])
                self.cltlevel = ttk.Combobox(self.pagewidgets["Clt"]["PageWin"]["PageStart"], values = tuple(clt_options['llevel']['choi']),
                                             width = 10, height = 10, font = self.customfonts['lst'], state = "readonly", name = 'llevel')
                self.cltlevel.set(clt_options['llevel']['def'])
                ToolTip(self.cltlevel, text = clt_options['llevel']['help'], wraplength = self.wraplength)
                # Logsize.
                cltsizelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Logsize: ', font = self.customfonts['opt'])
                self.cltsize = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.customfonts['opt'], name = 'lsize',
                                        validate = "key", validatecommand = self.validation_float)
                self.cltsize.insert('end', clt_options['lsize']['def'])
                ToolTip(self.cltsize, text = clt_options['lsize']['help'], wraplength = self.wraplength)
                # Asynchronous messages.
                self.chkvalcltasy = tk.BooleanVar()
                self.chkvalcltasy.set(clt_options['asyncmsg']['def'])
                chkcltasy = tk.Checkbutton(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Async\nMsg',
                                           font = self.customfonts['opt'], var = self.chkvalcltasy, relief = 'groove', name = 'asyncmsg')
                ToolTip(chkcltasy, text = clt_options['asyncmsg']['help'], wraplength = self.wraplength)

                # Listbox radiobuttons client.
                self.chkcltfile = ListboxOfRadiobuttons(self.pagewidgets["Clt"]["PageWin"]["PageStart"],
                                                        ['FILE', 'FILEOFF', 'STDOUT', 'STDOUTOFF', 'FILESTDOUT'],
                                                        self.customfonts['lst'],
                                                        changed = [(self.cltfile, clt_options['lfile']['def']),
                                                                   (cltfilebtnwin, ''),
                                                                   (self.cltsize, clt_options['lsize']['def']),
                                                                   (self.cltlevel, clt_options['llevel']['def'])],
                                                        width = 10, height = 1, borderwidth = 2, relief = 'ridge')
               
                ## Layout widgets (optcltwin:Clt:PageWin:PageStart)
                cltver.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = 'ew')
                cltipaddlbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltipadd.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltportlbl.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltport.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltmodelbl.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltmode.grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltcmidlbl.grid(row = 4, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltcmid.grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltnamelbl.grid(row = 5, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltname.grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltfilelbl.grid(row = 6, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltfile.grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltfilebtnwin.grid(row = 6, column = 2, padx = 5, pady = 5, sticky = 'ew')
                self.chkcltfile.grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'ew')
                chkcltasy.grid(row = 7, column = 2, padx = 5, pady = 5, sticky = 'ew')
                cltlevellbl.grid(row = 8, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltlevel.grid(row = 8, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltsizelbl.grid(row = 9, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltsize.grid(row = 9, column = 1, padx = 5, pady = 5, sticky = 'ew')

                # ugly fix when client-side mode is activated.
                templbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"],
                                   bg = self.customcolors['lavender']).grid(row = 10, column = 0,
                                                                            padx = 35, pady = 54, sticky = 'e')

                ## Create widgets (optcltwin:Clt:PageWin:PageEnd) -------------------------------------------------------------------------------------------
                # Timeout connection.
                clttimeout0lbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], text = 'Timeout connection: ', font = self.customfonts['opt'])
                self.clttimeout0 = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], width = 16, font = self.customfonts['opt'], name = 'time0')
                self.clttimeout0.insert('end', str(clt_options['time0']['def']))
                ToolTip(self.clttimeout0, text = clt_options['time0']['help'], wraplength = self.wraplength)
                # Timeout send/recv.
                clttimeout1lbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], text = 'Timeout send-recv: ', font = self.customfonts['opt'])
                self.clttimeout1 = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], width = 16, font = self.customfonts['opt'], name = 'time1')
                self.clttimeout1.insert('end', str(clt_options['time1']['def']))
                ToolTip(self.clttimeout1, text = clt_options['time1']['help'], wraplength = self.wraplength)

                ## Layout widgets (optcltwin:Clt:PageWin:PageEnd)
                # a label for vertical aligning with PageStart
                tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], width = 0,
                         height = 0, bg = self.customcolors['lavender']).grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nw')
                clttimeout0lbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.clttimeout0.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'w')
                clttimeout1lbl.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.clttimeout1.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'w')

                ## Store client-side widgets.
                self.storewidgets_clt = self.gui_store(side = "Clt", typewidgets = ['Button', 'Entry', 'TCombobox', 'Checkbutton'])
                self.storewidgets_clt.append(self.chkcltfile)
                
                ## Create widgets and layout (msgcltwin) -----------------------------------------------------------------------------------------------------
                self.textboxclt = TextDoubleScroll(self.msgcltwin, background = self.customcolors['black'], wrap = 'none', state = 'disabled',
                                                   relief = 'ridge', font = self.customfonts['msg'])
                self.textboxclt.put()
                               
        def prep_option(self, value):
                try:
                        # is an INT
                        return int(value)
                except (TypeError, ValueError):
                        try:
                                # is a FLOAT
                                return float(value)
                        except (TypeError, ValueError):
                                # is a STRING.
                                return value

        def prep_logfile(self, filepath, status):
                # FILE       (pretty on,  log view off, logfile yes)
                # FILEOFF    (pretty on,  log view off, no logfile)
                # STDOUT     (pretty off, log view on,  no logfile)
                # STDOUTOFF  (pretty off, log view off, logfile yes)
                # FILESTDOUT (pretty off, log view on,  logfile yes)

                if status == 'FILE':
                        return filepath
                elif status in ['FILESTDOUT', 'STDOUTOFF']:
                        return [status, filepath]
                elif status in ['STDOUT', 'FILEOFF']:
                        return status

        def validate_int(self, value):
                return value == "" or value.isdigit()

        def validate_float(self, value):
                if value == "":
                        return True
                try:
                        float(value)
                        return True
                except ValueError:
                        return False

        def clt_on_show(self, force_remove = False, force_view = False):
                if self.optcltwin.winfo_ismapped() or force_remove:
                        self.shbtnclt.configure(text = 'SHOW\nCLIENT', relief = 'raised')
                        self.optcltwin.grid_remove()
                        self.msgcltwin.grid_remove()
                        self.btncltwin.place_forget()
                elif not self.optcltwin.winfo_ismapped() or force_view:
                        self.shbtnclt.configure(text = 'HIDE\nCLIENT', relief = 'sunken')
                        self.optcltwin.grid()
                        self.msgcltwin.grid()
                        self.btncltwin.place(x = self.btncltwin_X, y = self.btncltwin_Y, bordermode = 'inside', anchor = 'nw')

        def srv_on_start(self):
                if self.runbtnsrv['text'] == 'START\nSERVER':
                        self.on_clear([txsrv, txclt])
                        self.srv_actions_start()
                        # wait for switch.
                        while not serverthread.is_running_server:
                                pass

                        self.srv_toggle_all(on_start = True)
                        # run thread for interrupting server when an error happens.
                        self.srv_eject_thread = threading.Thread(target = self.srv_eject, name = "Thread-SrvEjt")
                        self.srv_eject_thread.setDaemon(True)
                        self.srv_eject_thread.start()

                elif self.runbtnsrv['text'] == 'STOP\nSERVER':
                        serverthread.terminate_eject()

        def srv_eject(self):
                while not serverthread.eject:
                        sleep(0.1)
                self.srv_actions_stop()

        def srv_actions_start(self):
                srv_config[srv_options['ip']['des']] = self.srvipadd.get()
                srv_config[srv_options['port']['des']] = self.prep_option(self.srvport.get())
                srv_config[srv_options['epid']['des']] = self.epid.get()
                srv_config[srv_options['lcid']['des']] = self.prep_option(self.lcid.get())
                srv_config[srv_options['hwid']['des']] = self.hwid.get()
                srv_config[srv_options['count']['des']] = self.prep_option(self.count.get())
                srv_config[srv_options['activation']['des']] = self.prep_option(self.activ.get())
                srv_config[srv_options['renewal']['des']] = self.prep_option(self.renew.get())
                srv_config[srv_options['lfile']['des']] = self.prep_logfile(self.srvfile.get(), self.chksrvfile.state())
                srv_config[srv_options['asyncmsg']['des']] = self.chkvalsrvasy.get()
                srv_config[srv_options['llevel']['des']] = self.srvlevel.get()
                srv_config[srv_options['lsize']['des']] = self.prep_option(self.srvsize.get())

                srv_config[srv_options['time0']['des']] = self.prep_option(self.srvtimeout0.get())
                srv_config[srv_options['time1']['des']] = self.prep_option(self.srvtimeout1.get())
                srv_config[srv_options['sql']['des']] = (self.chkfilesql.get() if self.chkvalsql.get() else self.chkvalsql.get())

                ## Redirect stdout.
                gui_redirector('stdout', redirect_to = TextRedirect.Log,
                               redirect_conditio = (srv_config[srv_options['lfile']['des']] in ['STDOUT', 'FILESTDOUT']))
                serverqueue.put('start')

        def srv_actions_stop(self):
                if serverthread.is_running_server:
                        if serverthread.server is not None:
                                server_terminate(serverthread, exit_server = True)
                                # wait for switch.
                                while serverthread.is_running_server:
                                        pass
                        else:
                                serverthread.is_running_server = False
                        self.srv_toggle_all(on_start = False)
                        self.count_clear, self.keep_clear = (0, '0.0')

        def srv_toggle_all(self, on_start = True):
                self.srv_toggle_state()
                if on_start:
                        self.runbtnsrv.configure(text = 'STOP\nSERVER', background = self.customcolors['red'],
                                                 foreground = self.customcolors['white'], relief = 'sunken')
                        for widget in self.storewidgets_srv:
                                widget.configure(state = 'disabled')
                        self.runbtnclt.configure(state = 'normal')
                else:
                        self.runbtnsrv.configure(text = 'START\nSERVER', background = self.customcolors['green'],
                                         foreground = self.customcolors['white'], relief = 'raised')
                        for widget in self.storewidgets_srv:
                                widget.configure(state = 'normal')
                                if isinstance(widget, ListboxOfRadiobuttons):
                                        widget.change()
                        self.runbtnclt.configure(state = 'disabled')

        def srv_toggle_state(self):
                if serverthread.is_running_server:
                        txt, color = ('Server\nState:\nServing', self.customcolors['green'])
                else:
                        txt, color = ('Server\nState:\nStopped', self.customcolors['red'])
                        
                self.statesrv.configure(text = txt, foreground = color)

        def clt_on_start(self):
                if self.onlyclt:
                        self.on_clear([txclt])
                else:
                        rng, add_newline = self.on_clear_setup()
                        self.on_clear([txsrv, txclt], clear_range = [rng, None], newline_list = [add_newline, False])

                self.runbtnclt.configure(relief = 'sunken')
                self.clt_actions_start()
                # run thread for disabling interrupt server and client, when client running.
                self.clt_eject_thread = threading.Thread(target = self.clt_eject, name = "Thread-CltEjt")
                self.clt_eject_thread.setDaemon(True)
                self.clt_eject_thread.start()

                for widget in self.storewidgets_clt + [self.runbtnsrv, self.runbtnclt, self.defaubtnsrv]:
                        widget.configure(state = 'disabled')
                self.runbtnclt.configure(relief = 'raised')

        def clt_actions_start(self):
                clt_config[clt_options['ip']['des']] = self.cltipadd.get()
                clt_config[clt_options['port']['des']] = self.prep_option(self.cltport.get())
                clt_config[clt_options['mode']['des']] = self.cltmode.get()
                clt_config[clt_options['cmid']['des']] = self.cltcmid.get()
                clt_config[clt_options['name']['des']] = self.cltname.get()
                clt_config[clt_options['lfile']['des']] = self.prep_logfile(self.cltfile.get(), self.chkcltfile.state())
                clt_config[clt_options['asyncmsg']['des']] = self.chkvalcltasy.get()
                clt_config[clt_options['llevel']['des']] = self.cltlevel.get()
                clt_config[clt_options['lsize']['des']] = self.prep_option(self.cltsize.get())

                clt_config[clt_options['time0']['des']] = self.prep_option(self.clttimeout0.get())
                clt_config[clt_options['time1']['des']] = self.prep_option(self.clttimeout1.get())

                ## Redirect stdout.
                gui_redirector('stdout', redirect_to = TextRedirect.Log,
                               redirect_conditio = (clt_config[clt_options['lfile']['des']] in ['STDOUT', 'FILESTDOUT']))

                # run client (in a thread).
                self.clientthread = client_thread(name = "Thread-Clt")
                self.clientthread.setDaemon(True)
                self.clientthread.with_gui = True
                self.clientthread.start()

        def clt_eject(self):
                while self.clientthread.is_alive():
                        sleep(0.1)

                widgets = self.storewidgets_clt + [self.runbtnclt] + [self.defaubtnsrv]
                if not self.onlyclt:
                        widgets += [self.runbtnsrv]

                for widget in widgets:
                        if isinstance(widget, ttk.Combobox):
                                widget.configure(state = 'readonly')
                        else:
                                widget.configure(state = 'normal')
                                if isinstance(widget, ListboxOfRadiobuttons):
                                        widget.change()

        def on_browse(self, entrywidget, options):
                path = filedialog.askdirectory()
                if os.path.isdir(path):
                        entrywidget.delete('0', 'end')
                        entrywidget.insert('end', path + os.sep + os.path.basename(options['lfile']['def']))

        def on_exit(self):
                if serverthread.is_running_server:
                        if serverthread.server is not None:
                                server_terminate(serverthread, exit_server = True)
                        else:
                                serverthread.is_running_server = False
                server_terminate(serverthread, exit_thread = True)
                self.destroy()

        def on_clear_setup(self):
                if any(opt in ['STDOUT', 'FILESTDOUT'] for opt in srv_config[srv_options['lfile']['des']]):
                        add_newline = True
                        if self.count_clear == 0:
                                self.keep_clear = txsrv.index('end-1c')
                else:
                        add_newline = False
                        if self.count_clear == 0:
                                self.keep_clear = txsrv.index('end')

                rng = [self.keep_clear, 'end']
                self.count_clear += 1

                return rng, add_newline

        def on_clear(self, widget_list, clear_range = None, newline_list = []):
                if newline_list == []:
                        newline_list = len(widget_list) * [False]

                for num, couple in enumerate(zip(widget_list, newline_list)):
                        widget, add_n = couple
                        try:
                                ini, fin = clear_range[num]
                        except TypeError:
                                ini, fin = '1.0', 'end'

                        widget.configure(state = 'normal')
                        widget.delete(ini, fin)
                        if add_n:
                                widget.insert('end', '\n')
                        widget.configure(state = 'disabled')

        def on_defaults(self):

                def put_defaults(widgets, chkasy, listofradio, options):
                        for widget in widgets:
                                wclass, wname = widget.winfo_class(), widget.winfo_name()
                                if wname == '!checkbutton':
                                        continue

                                opt = options[wname]['def']
                                if wclass == 'Entry':
                                        widget.delete(0, 'end')
                                        if wname == 'sql':
                                                self.chkvalsql.set(opt)
                                                self.sql_status()
                                        else:
                                                widget.insert('end', (opt if isinstance(opt, str) else str(opt)))
                                elif wclass == 'Checkbutton':
                                        if wname == 'asyncmsg':
                                                chkasy.set(opt)
                                elif wclass == 'TCombobox':
                                        widget.set(str(opt))

                        # ListboxOfRadiobuttons default.
                        listofradio.radiovar.set('FILE')
                        listofradio.textbox.yview_moveto(0)
                        listofradio.change()

                if self.runbtnsrv['text'] == 'START\nSERVER':
                        apply_default = zip(["Srv", "Clt"],
                                            [self.chkvalsrvasy, self.chkvalcltasy],
                                            [self.chksrvfile, self.chkcltfile],
                                            [srv_options, clt_options])
                elif self.runbtnsrv['text'] == 'STOP\nSERVER':
                        apply_default = zip(*[("Clt",),
                                              (self.chkvalcltasy,),
                                              (self.chkcltfile,),
                                              (clt_options,)])

                for side, chkasy, listofradio, options in apply_default:
                        widgets = self.gui_store(side = side, typewidgets = ['Entry', 'TCombobox', 'Checkbutton'])
                        put_defaults(widgets, chkasy, listofradio, options)
