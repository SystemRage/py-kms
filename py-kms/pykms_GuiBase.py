#!/usr/bin/env python3

import os
import sys
import threading

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
        
from pykms_Server import srv_options, srv_version, srv_config, serverqueue, serverthread
from pykms_GuiMisc import ToolTip, TextDoubleScroll, TextRedirect, custom_background, make_clear
from pykms_Client import clt_options, clt_version, clt_config, clt_main

gui_description = 'py-kms GUI'
gui_version = 'v1.0'

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
                ip = ''
                print('Error: Couldn\'t get local ip')
        return ip

def switch_dir(path):
        if os.path.isdir(path):
                os.chdir(path)
                return True

        if path == '':
                os.chdir(os.getcwd())
                return True
        else:
                return
        
def gui_redirect(str_to_print):
        global txsrv, txclt, txcol, rclt
       
        try:
                TextRedirect.StdoutRedirect(txsrv, txclt, txcol, rclt, str_to_print)
        except:
                print(str_to_print)

##---------------------------------------------------------------------------------------------------------------------------------------------------------

class KmsGui(tk.Tk):        
        def browse(self, entrywidget, options):
                path = filedialog.askdirectory()
                if os.path.isdir(path):
                        entrywidget.delete('0', 'end')
                        entrywidget.insert('end', path + os.sep + os.path.basename(options['lfile']['def']))
                        
                        
        def __init__(self, *args, **kwargs):
                tk.Tk.__init__(self, *args, **kwargs)
                self.wraplength = 200
                                                                                                
                ## Define fonts and colors.
                self.btnwinfont = tkFont.Font(family = 'Times', size = 12, weight = 'bold')
                self.othfont = tkFont.Font(family = 'Times', size = 9, weight = 'bold')
                self.optfont = tkFont.Font(family = 'Helvetica', size = 11, weight = 'bold')
                self.msgfont = tkFont.Font(family = 'Helvetica', size = 7)

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
                self.gui_create()
                
        def gui_create(self):
                ## Create server gui
                self.gui_srv()
                ## Create client gui + other operations.
                self.gui_complete()
                ## Create globals for printing process (redirect stdout).
                global txsrv, txclt, txcol, rclt
                txsrv = self.textboxsrv.get()
                txclt = self.textboxclt.get()
                txcol = self.customcolors
                rclt = self.runbtnclt
                ## Redirect stderr.
                sys.stderr = TextRedirect.StderrRedirect(txsrv, txclt, txcol)
                
        def gui_srv(self):
                ## Create main containers. -------------------------------------------------------------------------------------------------------------
                self.masterwin = tk.Canvas(self, borderwidth = 3, relief = tk.RIDGE)
                self.btnsrvwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.optsrvwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                # self.optaddsrvwin = tk.Canvas(self.masterwin, background = self.customcolors['white'], borderwidth = 3, relief = 'ridge')
                self.msgsrvwin = tk.Frame(self.masterwin, background = self.customcolors['black'], relief = 'ridge', width = 300, height = 200)
               
                ## Layout main containers.
                self.masterwin.grid(row = 0, column = 0, sticky = 'nsew')
                self.btnsrvwin.grid(row = 0, column = 1, padx = 2, pady = 2, sticky = 'nw')
                self.optsrvwin.grid(row = 0, column = 2, padx = 2, pady = 2, sticky = 'nw')                
                # self.optaddsrvwin.grid(row = 0, column = 3, padx = 2, pady = 2, sticky = 'nw')
                self.msgsrvwin.grid(row = 1, column = 2, padx = 1, pady = 1, sticky = 'nsew')
                self.msgsrvwin.grid_propagate(False)
                self.msgsrvwin.grid_columnconfigure(0, weight = 1)
                self.msgsrvwin.grid_rowconfigure(0, weight = 1)

                ## Create widgets (btnsrvwin) -----------------------------------------------------------------------------------------------------------
                self.statesrv = tk.Label(self.btnsrvwin, text = 'Server\nState:\nStopped', font = self.othfont, foreground = self.customcolors['red'])
                self.runbtnsrv = tk.Button(self.btnsrvwin, text = 'START\nSERVER', background = self.customcolors['green'],
                                           foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.srv_clickedmain)
                self.shbtnclt = tk.Button(self.btnsrvwin, text = 'SHOW\nCLIENT', background = self.customcolors['magenta'],
                                          foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.clt_showhide)
                self.clearbtnsrv = tk.Button(self.btnsrvwin, text = 'CLEAR', background = self.customcolors['orange'],
                                             foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont,
                                             command = lambda: make_clear([txsrv, txclt]))
                self.exitbtnsrv = tk.Button(self.btnsrvwin, text = 'EXIT', background = self.customcolors['black'],
                                            foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont, command = self.destroy)
        
                ## Layout widgets (btnsrvwin)
                self.statesrv.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.runbtnsrv.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.shbtnclt.grid(row = 2, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.clearbtnsrv.grid(row = 3, column = 0, padx = 2, pady = 2, sticky = 'ew')
                self.exitbtnsrv.grid(row = 4, column = 0, padx = 2, pady = 2, sticky = 'ew')                
                
                ## Create widgets (optsrvwin) ------------------------------------------------------------------------------------------------------
                # Version.
                ver = tk.Label(self.optsrvwin, text = 'You are running server version: ' + srv_version, foreground = self.customcolors['red'],
                               font = self.othfont)
                # Ip Address.
                ipaddlbl = tk.Label(self.optsrvwin, text = 'IP Address: ', font = self.optfont)
                self.ipadd = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.ipadd.insert('end', srv_options['ip']['def'])
                ToolTip(self.ipadd, text = srv_options['ip']['help'], wraplength = self.wraplength)
                myipadd = tk.Label(self.optsrvwin, text = 'Your IP address is: {}'.format(get_ip_address()), foreground = self.customcolors['red'],
                                   font = self.othfont)
                # Port.
                portlbl = tk.Label(self.optsrvwin, text = 'Port: ', font = self.optfont)
                self.port = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.port.insert('end', str(srv_options['port']['def']))
                ToolTip(self.port, text = srv_options['port']['help'], wraplength = self.wraplength)
                # EPID.
                epidlbl = tk.Label(self.optsrvwin, text = 'EPID: ', font = self.optfont)
                self.epid = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.epid.insert('end', str(srv_options['epid']['def']))
                ToolTip(self.epid, text = srv_options['epid']['help'], wraplength = self.wraplength)
                # LCID.
                lcidlbl = tk.Label(self.optsrvwin, text = 'LCID: ', font = self.optfont)
                self.lcid = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.lcid.insert('end', str(srv_options['lcid']['def']))
                ToolTip(self.lcid, text = srv_options['lcid']['help'], wraplength = self.wraplength)
                # HWID.
                hwidlbl = tk.Label(self.optsrvwin, text = 'HWID: ', font = self.optfont)
                self.hwid = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.hwid.insert('end', srv_options['hwid']['def'])
                ToolTip(self.hwid, text = srv_options['hwid']['help'], wraplength = self.wraplength)
                # Client Count
                countlbl = tk.Label(self.optsrvwin, text = 'Client Count: ', font = self.optfont)
                self.count = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.count.insert('end', str(srv_options['count']['def']))
                ToolTip(self.count, text = srv_options['count']['help'], wraplength = self.wraplength)
                # Activation Interval.
                activlbl = tk.Label(self.optsrvwin, text = 'Activation Interval: ', font = self.optfont)
                self.activ = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.activ.insert('end', str(srv_options['activation']['def']))
                ToolTip(self.activ, text = srv_options['activation']['help'], wraplength = self.wraplength)
                # Renewal Interval.
                renewlbl = tk.Label(self.optsrvwin, text = 'Activation Interval: ', font = self.optfont)
                self.renew = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.renew.insert('end', str(srv_options['renewal']['def']))
                ToolTip(self.renew, text = srv_options['renewal']['help'], wraplength = self.wraplength)
                # Logfile.
                filelbl = tk.Label(self.optsrvwin, text = 'Logfile Path / Name: ', font = self.optfont)
                self.file = tk.Entry(self.optsrvwin, width = 10, font = self.optfont)
                self.file.insert('end', srv_options['lfile']['def'])
                ToolTip(self.file, text = srv_options['lfile']['help'], wraplength = self.wraplength)
                filebtnwin = tk.Button(self.optsrvwin, text = 'Browse', command = lambda: self.browse(self.file, srv_options))
                # Loglevel.
                levellbl = tk.Label(self.optsrvwin, text = 'Loglevel: ', font = self.optfont)
                self.level = ttk.Combobox(self.optsrvwin, values = tuple(srv_options['llevel']['choi']), width = 10)
                self.level.set(srv_options['llevel']['def'])
                ToolTip(self.level, text = srv_options['llevel']['help'], wraplength = self.wraplength)
                # Sqlite database.                
                self.chkval = tk.BooleanVar()
                self.chkval.set(srv_options['sql']['def'])
                chksql = tk.Checkbutton(self.optsrvwin, text = 'Create Sqlite\nDatabase', font = self.optfont, var = self.chkval)
                ToolTip(chksql, text = srv_options['sql']['help'], wraplength = self.wraplength)

                ## Layout widgets (optsrvwin)
                ver.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = 'ew')
                ipaddlbl.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.ipadd.grid(row = 1, column = 1, padx = 5, pady = 5, sticky = 'ew')
                myipadd.grid(row = 2, column = 1, columnspan = 2, padx = 5, pady = 5, sticky = 'ew')
                portlbl.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.port.grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'ew')
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
                filelbl.grid(row = 10, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.file.grid(row = 10, column = 1, padx = 5, pady = 5, sticky = 'ew')
                filebtnwin.grid(row = 10, column = 2, padx = 5, pady = 5, sticky = 'ew')
                levellbl.grid(row = 11, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.level.grid(row = 11, column = 1, padx = 5, pady = 5, sticky = 'ew')                
                chksql.grid(row = 12, column = 1, padx = 5, pady = 5, sticky = 'ew')

                ## Create widgets and layout (msgsrvwin) -----------------------------------------------------------------------------------------------
                self.textboxsrv = TextDoubleScroll(self.msgsrvwin, background = self.customcolors['black'], wrap = 'word', state = 'disabled',
                                                   relief = 'ridge', font = self.msgfont)
                self.textboxsrv.put()
                
                ## Create widgets (optaddsrvwin) -----------------------------------------------------------------------------------------------------
                # self.timeout = tk.Entry(self.optaddsrvwin, width = 10)
                # self.timeout.insert('end', '555')
                ## Layout widgets (optaddsrvwin)
                # self.timeout.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'e')
                                                        
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
                self.optcltwin.grid(row = 0, column = 4, padx = 2, pady = 2, sticky = 'nw')
                self.msgcltwin.grid(row = 1, column = 4, padx = 1, pady = 1, sticky = 'nsew')
                self.msgcltwin.grid_propagate(False)
                self.msgcltwin.grid_columnconfigure(0, weight = 1)
                self.msgcltwin.grid_rowconfigure(0, weight = 1)

                # Create widgets (btncltwin) ------------------------------------------------------------------------------------------------------------
                self.runbtnclt = tk.Button(self.btncltwin, text = 'START\nCLIENT', background = self.customcolors['blue'],
                                           foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont,
                                           state = 'disabled', command = self.clt_clickedstart)
                
                #self.othbutt = tk.Button(self.btncltwin, text = 'Botton\n2', background = self.customcolors['green'],
                #                               foreground = self.customcolors['white'], relief = 'flat', font = self.btnwinfont)
                
                # Layout widgets (btncltwin)
                self.runbtnclt.grid(row = 0, column = 0, padx = 2, pady = 2, sticky = 'ew')
                #self.othbutt.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'ew')
                
                # Create widgets (optcltwin) ------------------------------------------------------------------------------------------------------------
                # Version.
                cltver = tk.Label(self.optcltwin, text = 'You are running client version: ' + clt_version, foreground = self.customcolors['red'],
                                  font = self.othfont)
                # Ip Address.
                cltipaddlbl = tk.Label(self.optcltwin, text = 'IP Address: ', font = self.optfont)
                self.cltipadd = tk.Entry(self.optcltwin, width = 10, font = self.optfont)
                self.cltipadd.insert('end', clt_options['ip']['def'])
                ToolTip(self.cltipadd, text = clt_options['ip']['help'], wraplength = self.wraplength)
                # Port.
                cltportlbl = tk.Label(self.optcltwin, text = 'Port: ', font = self.optfont)
                self.cltport = tk.Entry(self.optcltwin, width = 10, font = self.optfont)
                self.cltport.insert('end', str(clt_options['port']['def']))
                ToolTip(self.cltport, text = clt_options['port']['help'], wraplength = self.wraplength)
                # Mode.
                cltmodelbl = tk.Label(self.optcltwin, text = 'Mode: ', font = self.optfont)
                self.cltmode = ttk.Combobox(self.optcltwin, values = tuple(clt_options['mode']['choi']), width = 10)
                self.cltmode.set(clt_options['mode']['def'])
                ToolTip(self.cltmode, text = clt_options['mode']['help'], wraplength = self.wraplength)
                # CMID.
                cltcmidlbl = tk.Label(self.optcltwin, text = 'CMID: ', font = self.optfont)
                self.cltcmid = tk.Entry(self.optcltwin, width = 10, font = self.optfont)
                self.cltcmid.insert('end', str(clt_options['cmid']['def']))
                ToolTip(self.cltcmid, text = clt_options['cmid']['help'], wraplength = self.wraplength)
                # Machine Name.
                cltnamelbl = tk.Label(self.optcltwin, text = 'Machine Name: ', font = self.optfont)
                self.cltname = tk.Entry(self.optcltwin, width = 10, font = self.optfont)
                self.cltname.insert('end', str(clt_options['name']['def']))
                ToolTip(self.cltname, text = clt_options['name']['help'], wraplength = self.wraplength)
                # Logfile.
                cltfilelbl = tk.Label(self.optcltwin, text = 'Logfile Path / Name: ', font = self.optfont)
                self.cltfile = tk.Entry(self.optcltwin, width = 10, font = self.optfont)
                self.cltfile.insert('end', clt_options['lfile']['def'])
                ToolTip(self.cltfile, text = clt_options['lfile']['help'], wraplength = self.wraplength)
                cltfilebtnwin = tk.Button(self.optcltwin, text = 'Browse', command = lambda: self.browse(self.cltfile, clt_options))
                # Loglevel.
                cltlevellbl = tk.Label(self.optcltwin, text = 'Loglevel: ', font = self.optfont)
                self.cltlevel = ttk.Combobox(self.optcltwin, values = tuple(clt_options['llevel']['choi']), width = 10)
                self.cltlevel.set(clt_options['llevel']['def'])
                ToolTip(self.cltlevel, text = clt_options['llevel']['help'], wraplength = self.wraplength)
               
                # Layout widgets (optcltwin)
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
                cltfilelbl.grid(row = 6, column = 0, padx = 5, pady = 5, sticky = 'ew')
                self.cltfile.grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'e')
                cltfilebtnwin.grid(row = 6, column = 2, padx = 5, pady = 5, sticky = 'ew')
                cltlevellbl.grid(row = 7, column = 0, padx = 5, pady = 5, sticky = 'e')
                self.cltlevel.grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'ew')
                
                # Create widgets and layout (msgcltwin) ----------------------------------------------------------------------------------------------------------
                self.textboxclt = TextDoubleScroll(self.msgcltwin, background = self.customcolors['black'], wrap = 'word', state = 'disabled',
                                                   relief = 'ridge', font = self.msgfont)
                self.textboxclt.put()
                               
        def proper_none(self, value):
                value = None if value == 'None' else value
                try:
                        return int(value)
                except TypeError:
                        return value
                       
        def clt_showhide(self, force = False):                
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

        def srv_clickedmain(self):
                if self.runbtnsrv['text'] == 'START\nSERVER':
                        if self.srv_clickedstart():
                                self.runbtnsrv.configure(text = 'STOP\nSERVER', background = self.customcolors['red'],
                                                         foreground = self.customcolors['white'])
                                self.runbtnclt.configure(state = 'normal')
                elif self.runbtnsrv['text'] == 'STOP\nSERVER':
                        self.srv_clickedstop()
                        self.runbtnsrv.configure(text = 'START\nSERVER', background = self.customcolors['green'],
                                                 foreground = self.customcolors['white'])
                        self.runbtnclt.configure(state = 'disabled')
                                                                       
        def srv_clickedstart(self):
                ok = False
                if switch_dir(os.path.dirname(self.file.get())):
                        if self.file.get().lower().endswith('.log'):
                                # Load dict.
                                srv_config[srv_options['ip']['des']] = self.ipadd.get()
                                srv_config[srv_options['port']['des']] = int(self.port.get())
                                srv_config[srv_options['epid']['des']] = self.proper_none(self.epid.get())
                                srv_config[srv_options['lcid']['des']] = int(self.lcid.get())
                                srv_config[srv_options['hwid']['des']] = self.hwid.get()
                                srv_config[srv_options['count']['des']] = self.proper_none(self.count.get())
                                srv_config[srv_options['activation']['des']] = int(self.activ.get())
                                srv_config[srv_options['renewal']['des']] = int(self.renew.get())
                                srv_config[srv_options['lfile']['des']] = self.file.get()
                                srv_config[srv_options['llevel']['des']] = self.level.get()
                                srv_config[srv_options['sql']['des']] = self.chkval.get()
                                ## TODO.
                                srv_config[srv_options['lsize']['des']] = 0
                                srv_config[srv_options['time']['des']] = 30

                                serverqueue.put('start')
                                # wait for switch.
                                while not serverthread.is_running:
                                        pass
                                self.srv_togglestate()
                                ok = True
                        else:
                                messagebox.showerror('Invalid extension', 'Not a .log file !')   
                else:
                        messagebox.showerror('Invalid path', 'Path you have provided not found !')
                return ok
                

        def srv_clickedstop(self):
                if serverthread.is_running:
                        serverqueue.put('stop')
                        serverthread.server.shutdown()
                        # wait for switch.
                        while serverthread.is_running:
                                pass
                        self.srv_togglestate()

        def srv_togglestate(self):
                if serverthread.is_running:
                        txt, color = ('Server\nState:\nServing', self.customcolors['green'])
                else:
                        txt, color = ('Server\nState:\nStopped', self.customcolors['red'])
                        
                self.statesrv.configure(text = txt, foreground = color)

        def clt_clickedstart(self):                                        
                if switch_dir(os.path.dirname(self.cltfile.get())):
                        if self.cltfile.get().lower().endswith('.log'):
                                # Load dict.
                                clt_config[clt_options['ip']['des']] = self.cltipadd.get()
                                clt_config[clt_options['port']['des']] = int(self.cltport.get())
                                clt_config[clt_options['mode']['des']] = self.cltmode.get()
                                clt_config[clt_options['cmid']['des']] = self.proper_none(self.cltcmid.get())
                                clt_config[clt_options['name']['des']] = self.proper_none(self.cltname.get())
                                clt_config[clt_options['lfile']['des']] = self.cltfile.get()
                                clt_config[clt_options['llevel']['des']] = self.cltlevel.get()
                                ## TODO
                                clt_config[clt_options['lsize']['des']] = 0

                                
                                clientthread = threading.Thread(target = clt_main, args=(True,))
                                clientthread.setDaemon(True)
                                clientthread.start()                                       
                        else:
                                messagebox.showerror('Invalid extension', 'Not a .log file !')   
                else:
                        messagebox.showerror('Invalid path', 'Path you have provided not found !')
