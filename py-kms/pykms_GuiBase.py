#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
from time import sleep

try:
        # Python 2.x imports
        import Tkinter as tk
        import ttk
        import tkMessageBox as messagebox
        import tkFileDialog as filedialog
        import tkFont
except ImportError:
        # Python 3.x imports
        import tkinter as tk
        from tkinter import ttk
        from tkinter import messagebox
        from tkinter import filedialog
        import tkinter.font as tkFont
        
from pykms_Server import srv_options, srv_version, srv_config, server_terminate, serverqueue, serverthread
from pykms_GuiMisc import ToolTip, TextDoubleScroll, TextRedirect, ListboxOfRadiobuttons
from pykms_GuiMisc import custom_background, custom_pages
from pykms_Client import clt_options, clt_version, clt_config, client_thread

gui_version             = "py-kms_gui_v2.0"
__license__             = "The Unlicense"
__author__              = u"Matteo ℱan <SystemRage@protonmail.com>"
__url__                 = "https://github.com/SystemRage/py-kms"
gui_description         = "A GUI for py-kms."

##---------------------------------------------------------------------------------------------------------------------------------------------------------
def get_ip_address():
        if os.name == 'posix':
                try:
                        # Python 2.x import
                        import commands 
                except ImportError:
                        #Python 3.x import
                        import subprocess as commands 
                ip = commands.getoutput("hostname -I")
        elif os.name == 'nt':
                import socket
                ip = socket.gethostbyname(socket.gethostname())
        else:
                ip = 'Unknown'
        return ip
        
def gui_redirect(str_to_print, where):
        global txsrv, txclt, txcol

        try:
                TextRedirect.StdoutRedirect(txsrv, txclt, txcol, str_to_print, where)
        except:
                print(str_to_print)

##-----------------------------------------------------------------------------------------------------------------------------------------------------------

class KmsGui(tk.Tk):        
        def browse(self, entrywidget, options):
                path = filedialog.askdirectory()
                if os.path.isdir(path):
                        entrywidget.delete('0', 'end')
                        entrywidget.insert('end', path + os.sep + os.path.basename(options['lfile']['def']))
                        
                        
        def __init__(self, *args, **kwargs):
                tk.Tk.__init__(self, *args, **kwargs)
                self.wraplength = 200
                serverthread.with_gui = True
                self.validation_int = (self.register(self.validate_int), "%S")
                self.validation_float = (self.register(self.validate_float), "%P")

                ## Define fonts and colors.
                self.btnwinfont = tkFont.Font(family = 'Times', size = 12, weight = 'bold')
                self.othfont = tkFont.Font(family = 'Times', size = 9, weight = 'bold')
                self.optfont = tkFont.Font(family = 'Helvetica', size = 11, weight = 'bold')
                self.optfontredux = tkFont.Font(family = 'Helvetica', size = 9, weight = 'bold')
                self.msgfont = tkFont.Font(family = 'Monospace', size = 6) # need a monospaced type (like courier, etc..).

                self.customcolors = { 'black'   : '#000000',
                                      'white'   : '#FFFFFF',
                                      'green'   : '#90EE90',
                                      'yellow'  : '#FFFF00',
                                      'magenta' : '#DA70D6',
                                      'orange'  : '#FFA500',
                                      'red'     : '#FF4500',
                                      'blue'    : '#1E90FF',
                                      'cyan'    : '#AFEEEE',
                                      'lavender': '#E6E6FA',
                                      }

                self.option_add('*TCombobox*Listbox.font', self.optfontredux)

                self.gui_create()
                
        def gui_create(self):
                ## Create server gui
                self.gui_srv()
                ## Create client gui + other operations.
                self.gui_complete()
                ## Create globals for printing process (redirect stdout).
                global txsrv, txclt, txcol
                txsrv = self.textboxsrv.get()
                txclt = self.textboxclt.get()
                txcol = self.customcolors
                ## Redirect stderr.
                sys.stderr = TextRedirect.StderrRedirect(txsrv, txclt, txcol)

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
                # customize buttons.
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

                ## subpages of optsrvwin.
                self.gui_pages_create(parent = self.optsrvwin, side = "Srv", create = {"PageStart": None,
                                                                                       "PageEnd": None})

                ## continue to grid.
                self.msgsrvwin.grid(row = 1, column = 2, padx = 1, pady = 1, sticky = 'nsew')
                self.msgsrvwin.grid_propagate(False)
                self.msgsrvwin.grid_columnconfigure(0, weight = 1)
                self.msgsrvwin.grid_rowconfigure(0, weight = 1)

                ## Create widgets (btnsrvwin) ---------------------------------------------------------------------------------------------------------------
                self.statesrv = tk.Label(self.btnsrvwin, text = 'Server\nState:\nStopped', font = self.othfont, foreground = self.customcolors['red'])
                self.runbtnsrv = tk.Button(self.btnsrvwin, text = 'START\nSERVER', background = self.customcolors['green'],
                                           foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.srv_on_start)
                self.shbtnclt = tk.Button(self.btnsrvwin, text = 'SHOW\nCLIENT', background = self.customcolors['magenta'],
                                          foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.clt_on_show)
                self.clearbtnsrv = tk.Button(self.btnsrvwin, text = 'CLEAR', background = self.customcolors['orange'],
                                             foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont,
                                             command = lambda: self.on_clear([txsrv, txclt]))
                self.exitbtnsrv = tk.Button(self.btnsrvwin, text = 'EXIT', background = self.customcolors['black'],
                                            foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.on_exit)
        
                ## Layout widgets (btnsrvwin)
                self.statesrv.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.runbtnsrv.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.shbtnclt.grid(row = 2, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.clearbtnsrv.grid(row = 3, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.exitbtnsrv.grid(row = 4, column = 0, padx = 2, pady = 2, sticky = 'ew')                
                
                ## Create widgets (optsrvwin:Srv:PageWin:PageStart) -----------------------------------------------------------------------------------------
                # Version.
                ver = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"],
                               text = 'You are running server version: ' + srv_version, foreground = self.customcolors['red'],
                               font = self.othfont)
                # Ip Address.
                srvipaddlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'IP Address: ', font = self.optfont)
                self.srvipadd = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.srvipadd.insert('end', srv_options['ip']['def'])
                ToolTip(self.srvipadd, text = srv_options['ip']['help'], wraplength = self.wraplength)
                myipadd = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Your IP address is: {}'.format(get_ip_address()),
                                   foreground = self.customcolors['red'], font = self.othfont)
                # Port.
                srvportlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Port: ', font = self.optfont)
                self.srvport = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                        validatecommand = self.validation_int)
                self.srvport.insert('end', str(srv_options['port']['def']))
                ToolTip(self.srvport, text = srv_options['port']['help'], wraplength = self.wraplength)
                # EPID.
                epidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'EPID: ', font = self.optfont)
                self.epid = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.epid.insert('end', str(srv_options['epid']['def']))
                ToolTip(self.epid, text = srv_options['epid']['help'], wraplength = self.wraplength)
                # LCID.
                lcidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'LCID: ', font = self.optfont)
                self.lcid = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                     validatecommand = self.validation_int)
                self.lcid.insert('end', str(srv_options['lcid']['def']))
                ToolTip(self.lcid, text = srv_options['lcid']['help'], wraplength = self.wraplength)
                # HWID.
                hwidlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'HWID: ', font = self.optfont)
                self.hwid = ttk.Combobox(self.pagewidgets["Srv"]["PageWin"]["PageStart"], values = (str(srv_options['hwid']['def']), 'RANDOM'),
                                         width = 17, height = 10, font = self.optfontredux)
                self.hwid.set(str(srv_options['hwid']['def']))
                ToolTip(self.hwid, text = srv_options['hwid']['help'], wraplength = self.wraplength)
                # Client Count
                countlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Client Count: ', font = self.optfont)
                self.count = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.count.insert('end', str(srv_options['count']['def']))
                ToolTip(self.count, text = srv_options['count']['help'], wraplength = self.wraplength)
                # Activation Interval.
                activlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Activation Interval: ', font = self.optfont)
                self.activ = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                      validatecommand = self.validation_int)
                self.activ.insert('end', str(srv_options['activation']['def']))
                ToolTip(self.activ, text = srv_options['activation']['help'], wraplength = self.wraplength)
                # Renewal Interval.
                renewlbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Activation Interval: ', font = self.optfont)
                self.renew = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                      validatecommand = self.validation_int)
                self.renew.insert('end', str(srv_options['renewal']['def']))
                ToolTip(self.renew, text = srv_options['renewal']['help'], wraplength = self.wraplength)
                # Logfile.
                srvfilelbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Logfile Path / Name: ', font = self.optfont)
                self.srvfile = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.srvfile.insert('end', srv_options['lfile']['def'])
                self.srvfile.xview_moveto(1)
                ToolTip(self.srvfile, text = srv_options['lfile']['help'], wraplength = self.wraplength)
                srvfilebtnwin = tk.Button(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Browse',
                                       command = lambda: self.browse(self.srvfile, srv_options))

                # Loglevel.
                srvlevellbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Loglevel: ', font = self.optfont)
                self.srvlevel = ttk.Combobox(self.pagewidgets["Srv"]["PageWin"]["PageStart"], values = tuple(srv_options['llevel']['choi']),
                                             width = 10, height = 10, font = self.optfontredux, state = "readonly")
                self.srvlevel.set(srv_options['llevel']['def'])
                ToolTip(self.srvlevel, text = srv_options['llevel']['help'], wraplength = self.wraplength)

                self.chksrvfile = ListboxOfRadiobuttons(self.pagewidgets["Srv"]["PageWin"]["PageStart"],
                                                        ['FILE', 'FILEOFF', 'STDOUT', 'STDOUTOFF', 'FILESTDOUT'],
                                                        self.optfontredux,
                                                        changed = [(self.srvfile, srv_options['lfile']['def']),
                                                                   (srvfilebtnwin, ''),
                                                                   (self.srvlevel, srv_options['llevel']['def'])],
                                                        width = 10, height = 1, borderwidth = 2, relief = 'ridge')

                # Logsize.
                srvsizelbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageStart"], text = 'Logsize: ', font = self.optfont)
                self.srvsize = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                        validatecommand = self.validation_float)
                self.srvsize.insert('end', srv_options['lsize']['def'])
                ToolTip(self.srvsize, text = srv_options['lsize']['help'], wraplength = self.wraplength)

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
                srvlevellbl.grid(row = 12, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvlevel.grid(row = 12, column = 1, padx = 5, pady = 5, sticky = 'ew')
                srvsizelbl.grid(row = 13, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.srvsize.grid(row = 13, column = 1, padx = 5, pady = 5, sticky = 'ew')

                ## Create widgets (optsrvwin:Srv:PageWin:PageEnd)-------------------------------------------------------------------------------------------
                # Timeout connection.
                timeout0lbl = tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], text = 'Timeout connection: ', font = self.optfont)
                self.timeout0 = tk.Entry(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 10, font = self.optfont)
                self.timeout0.insert('end', str(srv_options['time0']['def']))
                ToolTip(self.timeout0, text = srv_options['time0']['help'], wraplength = self.wraplength)
                # Sqlite database.
                self.chkvalsql = tk.BooleanVar()
                self.chkvalsql.set(srv_options['sql']['def'])
                chksql = tk.Checkbutton(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], text = 'Create Sqlite\nDatabase',
                                        font = self.optfont, var = self.chkvalsql)
                ToolTip(chksql, text = srv_options['sql']['help'], wraplength = self.wraplength)

                ## Layout widgets (optsrvwin:Srv:PageWin:PageEnd)
                tk.Label(self.pagewidgets["Srv"]["PageWin"]["PageEnd"], width = 0, height = 0).grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nw')
                timeout0lbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.timeout0.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'ew')
                chksql.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'ew')

                # Store Srv widgets.
                self.storewidgets_srv = self.gui_store(side = "Srv", typewidgets = ['Button', 'Entry', 'TCombobox', 'Checkbutton'])
                self.storewidgets_srv.append(self.chksrvfile)

                ## Create widgets and layout (msgsrvwin) ---------------------------------------------------------------------------------------------------
                self.textboxsrv = TextDoubleScroll(self.msgsrvwin, background = self.customcolors['black'], wrap = 'none', state = 'disabled',
                                                   relief = 'ridge', font = self.msgfont)
                self.textboxsrv.put()

        def gui_complete(self):
                ## Create client widgets (optcltwin, msgcltwin, btncltwin)
                self.update_idletasks()   # update Gui to get btnsrvwin values --> btncltwin.
                self.iconify()  
                self.gui_clt()
                minw, minh = self.winfo_width(), self.winfo_height()
                # Main window custom background.
                self.update_idletasks()   # update Gui for custom background
                self.iconify()
                custom_background(self)
                # Main window other modifications.
                self.wm_attributes("-topmost", True)
                self.protocol("WM_DELETE_WINDOW", lambda:0) 
                self.minsize(minw, minh)
                self.resizable(True, False)
                
        def get_position(self, genericwidget):
                x, y = (genericwidget.winfo_x(), genericwidget.winfo_y())
                w, h = (genericwidget.winfo_width(), genericwidget.winfo_height())
                return x, y, w, h
                
        def gui_clt(self):                
                self.optcltwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.msgcltwin = tk.Frame(self.masterwin, background = self.customcolors['black'], relief = 'ridge', width = 300, height = 200)
                self.btncltwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                
                xb, yb, wb, hb = self.get_position(self.btnsrvwin)
                self.btncltwin_X = xb + 2
                self.btncltwin_Y = yb + hb + 10
                self.btncltwin.place(x = self.btncltwin_X, y = self.btncltwin_Y, bordermode = 'inside', anchor = 'nw')
                self.optcltwin.grid(row = 0, column = 4, padx = 2, pady = 2, sticky = 'nsew')
                self.optcltwin.grid_rowconfigure(0, weight = 1)
                self.optcltwin.grid_columnconfigure(1, weight = 1)

                # subpages of optcltwin.
                self.gui_pages_create(parent = self.optcltwin, side = "Clt", create = {"PageStart": None,
                                                                                       "PageEnd": None})

                # continue to grid.
                self.msgcltwin.grid(row = 1, column = 4, padx = 1, pady = 1, sticky = 'nsew')
                self.msgcltwin.grid_propagate(False)
                self.msgcltwin.grid_columnconfigure(0, weight = 1)
                self.msgcltwin.grid_rowconfigure(0, weight = 1)

                # Create widgets (btncltwin) ----------------------------------------------------------------------------------------------------------------
                self.runbtnclt = tk.Button(self.btncltwin, text = 'START\nCLIENT', background = self.customcolors['blue'],
                                           foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont,
                                           state = 'disabled', command = self.clt_on_start)
                
##                self.othbutt = tk.Button(self.btncltwin, text = 'Botton\n2', background = self.customcolors['green'],
##                                         foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont)
                
                # Layout widgets (btncltwin)
                self.runbtnclt.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
##                self.othbutt.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'ew')
                
                # Create widgets (optcltwin:Clt:PageWin:PageStart) ------------------------------------------------------------------------------------------
                # Version.
                cltver = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'You are running client version: ' + clt_version,
                                  foreground = self.customcolors['red'], font = self.othfont)
                # Ip Address.
                cltipaddlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'IP Address: ', font = self.optfont)
                self.cltipadd = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.cltipadd.insert('end', clt_options['ip']['def'])
                ToolTip(self.cltipadd, text = clt_options['ip']['help'], wraplength = self.wraplength)
                # Port.
                cltportlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Port: ', font = self.optfont)
                self.cltport = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                        validatecommand = self.validation_int)
                self.cltport.insert('end', str(clt_options['port']['def']))
                ToolTip(self.cltport, text = clt_options['port']['help'], wraplength = self.wraplength)
                # Mode.
                cltmodelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Mode: ', font = self.optfont)
                self.cltmode = ttk.Combobox(self.pagewidgets["Clt"]["PageWin"]["PageStart"], values = tuple(clt_options['mode']['choi']),
                                            width = 17, height = 10, font = self.optfontredux, state = "readonly")
                self.cltmode.set(clt_options['mode']['def'])
                ToolTip(self.cltmode, text = clt_options['mode']['help'], wraplength = self.wraplength)
                # CMID.
                cltcmidlbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'CMID: ', font = self.optfont)
                self.cltcmid = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.cltcmid.insert('end', str(clt_options['cmid']['def']))
                ToolTip(self.cltcmid, text = clt_options['cmid']['help'], wraplength = self.wraplength)
                # Machine Name.
                cltnamelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Machine Name: ', font = self.optfont)
                self.cltname = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.cltname.insert('end', str(clt_options['name']['def']))
                ToolTip(self.cltname, text = clt_options['name']['help'], wraplength = self.wraplength)
                # Logfile.
                cltfilelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Logfile Path / Name: ', font = self.optfont)
                self.cltfile = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont)
                self.cltfile.insert('end', clt_options['lfile']['def'])
                self.cltfile.xview_moveto(1)
                ToolTip(self.cltfile, text = clt_options['lfile']['help'], wraplength = self.wraplength)
                cltfilebtnwin = tk.Button(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Browse',
                                          command = lambda: self.browse(self.cltfile, clt_options))
                # Loglevel.
                cltlevellbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Loglevel: ', font = self.optfont)
                self.cltlevel = ttk.Combobox(self.pagewidgets["Clt"]["PageWin"]["PageStart"], values = tuple(clt_options['llevel']['choi']),
                                             width = 10, height = 10, font = self.optfontredux, state = "readonly")
                self.cltlevel.set(clt_options['llevel']['def'])
                ToolTip(self.cltlevel, text = clt_options['llevel']['help'], wraplength = self.wraplength)

                self.chkcltfile = ListboxOfRadiobuttons(self.pagewidgets["Clt"]["PageWin"]["PageStart"],
                                                        ['FILE', 'FILEOFF', 'STDOUT', 'STDOUTOFF', 'FILESTDOUT'],
                                                        self.optfontredux,
                                                        changed = [(self.cltfile, clt_options['lfile']['def']),
                                                                   (cltfilebtnwin, ''),
                                                                   (self.cltlevel, clt_options['llevel']['def'])],
                                                        width = 10, height = 1, borderwidth = 2, relief = 'ridge')
                # Logsize.
                cltsizelbl = tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageStart"], text = 'Logsize: ', font = self.optfont)
                self.cltsize = tk.Entry(self.pagewidgets["Clt"]["PageWin"]["PageStart"], width = 10, font = self.optfont, validate = "key",
                                        validatecommand = self.validation_float)
                self.cltsize.insert('end', clt_options['lsize']['def'])
                ToolTip(self.cltsize, text = clt_options['lsize']['help'], wraplength = self.wraplength)
               
                # Layout widgets (optcltwin:Clt:PageWin:PageStart)
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
                cltlevellbl.grid(row = 8, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltlevel.grid(row = 8, column = 1, padx = 5, pady = 5, sticky = 'ew')
                cltsizelbl.grid(row = 9, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltsize.grid(row = 9, column = 1, padx = 5, pady = 5, sticky = 'ew')

                ## Create widgets (optcltwin:Clt:PageWin:PageEnd) -------------------------------------------------------------------------------------------

                ## Layout widgets (optcltwin:Clt:PageWin:PageEnd)
                tk.Label(self.pagewidgets["Clt"]["PageWin"]["PageEnd"], width = 0, height = 0).grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'nw')

                # Store Clt widgets.
                self.storewidgets_clt = self.gui_store(side = "Clt", typewidgets = ['Button', 'Entry', 'TCombobox'])
                self.storewidgets_clt.append(self.chkcltfile)
                
                # Create widgets and layout (msgcltwin) -----------------------------------------------------------------------------------------------------
                self.textboxclt = TextDoubleScroll(self.msgcltwin, background = self.customcolors['black'], wrap = 'none', state = 'disabled',
                                                   relief = 'ridge', font = self.msgfont)
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

        def prep_logfile(self, filepath):
                # FILE       (pretty on,  log view off, logfile yes)
                # FILEOFF    (pretty on,  log view off, no logfile)
                # STDOUT     (pretty off, log view on,  no logfile)
                # STDOUTOFF  (pretty off, log view off, logfile yes)
                # FILESTDOUT (pretty off, log view on,  logfile yes)
                st = self.chksrvfile.state()
                if st == 'FILE':
                        return filepath
                elif st in ['FILESTDOUT', 'STDOUTOFF']:
                        return [st, filepath]
                elif st in ['STDOUT', 'FILEOFF']:
                        return st

        def validate_int(self, value):
                return value == '' or value.isdigit()

        def validate_float(self, value):
                if value == "":
                        return True
                try:
                        float(value)
                        return True
                except ValueError:
                        return False

        def clt_on_show(self, force = False):
                if self.optcltwin.winfo_ismapped() or force:
                        self.shbtnclt['text'] = 'SHOW\nCLIENT'
                        self.optcltwin.grid_remove()
                        self.msgcltwin.grid_remove()
                        self.btncltwin.place_forget()
                else:
                        self.shbtnclt['text'] = 'HIDE\nCLIENT'
                        self.optcltwin.grid()
                        self.msgcltwin.grid()
                        self.btncltwin.place(x = self.btncltwin_X, y = self.btncltwin_Y, bordermode = 'inside', anchor = 'nw')

        def srv_on_start(self):
                if self.runbtnsrv['text'] == 'START\nSERVER':
                        self.srv_actions_start()
                        # wait for switch.
                        while not serverthread.is_running_server:
                                pass

                        self.on_clear([txsrv, txclt])
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
                srv_config[srv_options['lfile']['des']] = self.prep_logfile(self.srvfile.get())
                srv_config[srv_options['llevel']['des']] = self.srvlevel.get()
                srv_config[srv_options['sql']['des']] = self.chkvalsql.get()
                srv_config[srv_options['lsize']['des']] = self.prep_option(self.srvsize.get())
                srv_config[srv_options['time0']['des']] = self.prep_option(self.timeout0.get())

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

        def srv_toggle_all(self, on_start = True):
                self.srv_toggle_state()
                if on_start:
                        self.runbtnsrv.configure(text = 'STOP\nSERVER', background = self.customcolors['red'],
                                                 foreground = self.customcolors['white'])
                        for widget in self.storewidgets_srv:
                                widget.configure(state = 'disabled')
                        self.runbtnclt.configure(state = 'normal')
                else:
                        self.runbtnsrv.configure(text = 'START\nSERVER', background = self.customcolors['green'],
                                         foreground = self.customcolors['white'])
                        for widget in self.storewidgets_srv:
                                widget.configure(state = 'normal')
                        self.runbtnclt.configure(state = 'disabled')

        def srv_toggle_state(self):
                if serverthread.is_running_server:
                        txt, color = ('Server\nState:\nServing', self.customcolors['green'])
                else:
                        txt, color = ('Server\nState:\nStopped', self.customcolors['red'])
                        
                self.statesrv.configure(text = txt, foreground = color)

        def clt_on_start(self):
                self.clt_actions_start()
                # run thread for disabling interrupt server and client, when client running.
                self.clt_eject_thread = threading.Thread(target = self.clt_eject, name = "Thread-CltEjt")
                self.clt_eject_thread.setDaemon(True)
                self.clt_eject_thread.start()

                self.on_clear([txsrv, txclt])
                for widget in self.storewidgets_clt + [self.runbtnsrv, self.runbtnclt]:
                        widget.configure(state = 'disabled')

        def clt_actions_start(self):
                clt_config[clt_options['ip']['des']] = self.cltipadd.get()
                clt_config[clt_options['port']['des']] = self.prep_option(self.cltport.get())
                clt_config[clt_options['mode']['des']] = self.cltmode.get()
                clt_config[clt_options['cmid']['des']] = self.cltcmid.get()
                clt_config[clt_options['name']['des']] = self.cltname.get()
                clt_config[clt_options['llevel']['des']] = self.cltlevel.get()
                clt_config[clt_options['lfile']['des']] = self.prep_logfile(self.cltfile.get())
                clt_config[clt_options['lsize']['des']] = self.prep_option(self.cltsize.get())

                # run client (in a thread).
                self.clientthread = client_thread(name = "Thread-Clt")
                self.clientthread.setDaemon(True)
                self.clientthread.with_gui = True
                self.clientthread.start()

        def clt_eject(self):
                while self.clientthread.is_alive():
                        sleep(0.1)
                for widget in self.storewidgets_clt + [self.runbtnsrv, self.runbtnclt]:
                        widget.configure(state = 'normal')

        def on_exit(self):
                if serverthread.is_running_server:
                        if serverthread.server is not None:
                                server_terminate(serverthread, exit_server = True)
                        else:
                                serverthread.is_running_server = False
                server_terminate(serverthread, exit_thread = True)
                self.destroy()

        def on_clear(self, widgetlist):
                for widget in widgetlist:
                        widget.configure(state = 'normal')
                        widget.delete('1.0', 'end')
                        widget.configure(state = 'disabled')
