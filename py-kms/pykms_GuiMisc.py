#!/usr/bin/env python3

import os
import re
import sys
from collections import Counter
from time import sleep
import threading
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

from pykms_Format import MsgMap, unshell_message, unformat_message

#------------------------------------------------------------------------------------------------------------------------------------------------------------

# https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
class ToolTip(object):
        """ Create a tooltip for a given widget """
        def __init__(self, widget, bg = '#FFFFEA', pad = (5, 3, 5, 3), text = 'widget info', waittime = 400, wraplength = 250):
                self.waittime = waittime  # ms
                self.wraplength = wraplength  # pixels
                self.widget = widget
                self.text = text
                self.widget.bind("<Enter>", self.onEnter)
                self.widget.bind("<Leave>", self.onLeave)
                self.widget.bind("<ButtonPress>", self.onLeave)
                self.bg = bg
                self.pad = pad
                self.id = None
                self.tw = None
        
        def onEnter(self, event = None):
                self.schedule() 

        def onLeave(self, event = None):
                self.unschedule()
                self.hide()

        def schedule(self):
                self.unschedule()
                self.id = self.widget.after(self.waittime, self.show)

        def unschedule(self):
                id_ = self.id
                self.id = None
                if id_:
                        self.widget.after_cancel(id_)
        
        def show(self):
                def tip_pos_calculator(widget, label, tip_delta = (10, 5), pad = (5, 3, 5, 3)):
                    w = widget
                    s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()
                    width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                                     pad[1] + label.winfo_reqheight() + pad[3])
                    mouse_x, mouse_y = w.winfo_pointerxy()
                    x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
                    x2, y2 = x1 + width, y1 + height

                    x_delta = x2 - s_width
                    if x_delta < 0:
                            x_delta = 0
                    y_delta = y2 - s_height
                    if y_delta < 0:
                            y_delta = 0

                    offscreen = (x_delta, y_delta) != (0, 0)

                    if offscreen:
                        if x_delta:
                                x1 = mouse_x - tip_delta[0] - width
                        if y_delta:
                                y1 = mouse_y - tip_delta[1] - height

                    offscreen_again = y1 < 0  # out on the top

                    if offscreen_again:
                        # No further checks will be done.

                        # TIP:
                        # A further mod might automagically augment the
                        # wraplength when the tooltip is too high to be
                        # kept inside the screen.
                        y1 = 0

                    return x1, y1

                bg = self.bg
                pad = self.pad
                widget = self.widget

                # creates a toplevel window
                self.tw = tk.Toplevel(widget)

                # leaves only the label and removes the app window
                self.tw.wm_overrideredirect(True)

                win = tk.Frame(self.tw, background = bg, borderwidth = 0)
                label = ttk.Label(win, text = self.text, justify = tk.LEFT, background = bg, relief = tk.SOLID, borderwidth = 0,
                                  wraplength = self.wraplength)
                label.grid(padx = (pad[0], pad[2]), pady = (pad[1], pad[3]), sticky=tk.NSEW)
                win.grid()

                x, y = tip_pos_calculator(widget, label)

                self.tw.wm_geometry("+%d+%d" % (x, y))
                
        def hide(self):
                tw = self.tw
                if tw:
                    tw.destroy()
                self.tw = None

##-----------------------------------------------------------------------------------------------------------------------------------------------------------

class TextRedirect(object):
        class Pretty(object):
                grpmsg = unformat_message([MsgMap[1], MsgMap[7], MsgMap[12], MsgMap[20]])
                arrows = [ item[0] for item in grpmsg  ]
                clt_msg_nonewline = [ item[1] for item in grpmsg ]
                arrows = list(set(arrows))
                lenarrow = len(arrows[0])
                srv_msg_nonewline = [ item[0] for item in unformat_message([MsgMap[2], MsgMap[5], MsgMap[13], MsgMap[18]]) ]
                msg_align = [ msg[0].replace('\t', '').replace('\n', '') for msg in unformat_message([MsgMap[-2], MsgMap[-4]]) ]

                def __init__(self, srv_text_space, clt_text_space, customcolors):
                        self.srv_text_space = srv_text_space
                        self.clt_text_space = clt_text_space
                        self.customcolors = customcolors

                def textbox_write(self, tag, message, color, extras):
                        widget = self.textbox_choose(message)
                        self.w_maxpix, self.h_maxpix = widget.winfo_width(), widget.winfo_height()
                        self.xfont = tkFont.Font(font = widget['font'])
                        widget.configure(state = 'normal')
                        widget.insert('end', self.textbox_format(message), tag)
                        self.textbox_color(tag, widget, color, self.customcolors['black'], extras)
                        widget.after(100, widget.see('end'))
                        widget.configure(state = 'disabled')

                def textbox_choose(self, message):
                        if any(item.startswith('logsrv') for item in [message, self.str_to_print]):
                                self.srv_text_space.focus_set()
                                self.where = "srv"
                                return self.srv_text_space
                        elif any(item.startswith('logclt') for item in [message, self.str_to_print]):
                                self.clt_text_space.focus_set()
                                self.where = "clt"
                                return self.clt_text_space

                def textbox_color(self, tag, widget, forecolor = 'white', backcolor = 'black', extras = []):
                        for extra in extras:
                                if extra == 'bold':
                                        self.xfont.configure(weight = "bold")
                                elif extra == 'italic':
                                        self.xfont.configure(slant = "italic")
                                elif extra == 'underlined':
                                        self.xfont.text_font.configure(underline = True)
                                elif extra == 'strike':
                                        self.xfont.configure(overstrike = True)
                                elif extra == 'reverse':
                                        forecolor, backcolor = backcolor, forecolor

                        widget.tag_configure(tag, foreground = forecolor, background = backcolor, font = self.xfont)
                        widget.tag_add(tag, "insert linestart", "insert lineend")

                def textbox_newline(self, message):
                        if not message.endswith('\n'):
                                return message + '\n'
                        else:
                                return message

                def textbox_format(self, message):
                        # vertical align.
                        self.w_maxpix = self.w_maxpix - 5 # pixel reduction for distance from border.
                        w_fontpix, h_fontpix = (self.xfont.measure('0'), self.xfont.metrics('linespace'))
                        msg_unformat = message.replace('\t', '').replace('\n', '')
                        lenfixed_chars = int((self.w_maxpix / w_fontpix) - len(msg_unformat))

                        if message in self.srv_msg_nonewline + self.clt_msg_nonewline:
                                lung = lenfixed_chars - self.lenarrow
                                if message in self.clt_msg_nonewline:
                                        message = self.textbox_newline(message)
                        else:
                                lung = lenfixed_chars
                                if (self.where == "srv") or (self.where == "clt" and message not in self.arrows):
                                         message = self.textbox_newline(message)
                                # horizontal align.
                                if msg_unformat in self.msg_align:
                                        msg_strip = message.lstrip('\n')
                                        message = '\n' * (len(message) - len(msg_strip) + TextRedirect.Pretty.newlinecut[0]) + msg_strip
                                        TextRedirect.Pretty.newlinecut.pop(0)

                        count = Counter(message)
                        countab = (count['\t'] if count['\t'] != 0 else 1)
                        message = message.replace('\t' * countab, ' ' * lung)
                        return message

                def textbox_do(self):
                        msgs, TextRedirect.Pretty.tag_num = unshell_message(self.str_to_print, TextRedirect.Pretty.tag_num)
                        for tag in msgs:
                                self.textbox_write(tag, msgs[tag]['text'], self.customcolors[msgs[tag]['color']], msgs[tag]['extra'])

                def flush(self):
                        pass

                def write(self, string):
                        if string != '\n':
                                self.str_to_print = string
                                self.textbox_do()

        class Stderr(Pretty):
                def __init__(self, srv_text_space, clt_text_space, customcolors, side):
                        self.srv_text_space = srv_text_space
                        self.clt_text_space = clt_text_space
                        self.customcolors = customcolors
                        self.side = side
                        self.tag_err = 'STDERR'
                        self.xfont = tkFont.Font(font = self.srv_text_space['font'])

                def textbox_choose(self, message):
                        if self.side == "srv":
                                return self.srv_text_space
                        elif self.side == "clt":
                                return self.clt_text_space
                                                
                def write(self, string):
                        widget = self.textbox_choose(string)
                        self.textbox_color(self.tag_err, widget, self.customcolors['red'], self.customcolors['black'])
                        self.srv_text_space.configure(state = 'normal')
                        self.srv_text_space.insert('end', string, self.tag_err)
                        self.srv_text_space.see('end')
                        self.srv_text_space.configure(state = 'disabled')

        class Log(Pretty):
                def textbox_format(self, message):
                        if message.startswith('logsrv'):
                                message = message.replace('logsrv ', '')
                        if message.startswith('logclt'):
                                message = message.replace('logclt ', '')
                        return message + '\n'
                
##-----------------------------------------------------------------------------------------------------------------------------------------------------------
class TextDoubleScroll(tk.Frame): 
        def __init__(self, master, **kwargs):
                """ Initialize.
                        - horizontal scrollbar
                        - vertical scrollbar
                        - text widget
                """
                tk.Frame.__init__(self, master)
                self.master = master
                
                self.textbox = tk.Text(self.master, **kwargs)
                self.sizegrip = ttk.Sizegrip(self.master)
                self.hs = ttk.Scrollbar(self.master, orient = "horizontal", command = self.on_scrollbar_x)
                self.vs = ttk.Scrollbar(self.master, orient = "vertical", command = self.on_scrollbar_y)
                self.textbox.configure(yscrollcommand = self.on_textscroll, xscrollcommand = self.hs.set)

        def on_scrollbar_x(self, *args):
                """ Horizontally scrolls text widget. """
                self.textbox.xview(*args)

        def on_scrollbar_y(self, *args):
                """ Vertically scrolls text widget. """
                self.textbox.yview(*args)
        
        def on_textscroll(self, *args):
                """ Moves the scrollbar and scrolls text widget when the mousewheel is moved on a text widget. """
                self.vs.set(*args)
                self.on_scrollbar_y('moveto', args[0])
        
        def put(self, **kwargs):
                """ Grid the scrollbars and textbox correctly. """
                self.textbox.grid(row = 0, column = 0, padx = 3, pady = 3, sticky = "nsew")
                self.vs.grid(row = 0, column = 1, sticky = "ns")
                self.hs.grid(row = 1, column = 0, sticky = "we")
                self.sizegrip.grid(row = 1, column = 1, sticky = "news")
                
        def get(self):
                """ Return the "frame" useful to place inner controls. """
                return self.textbox

##-----------------------------------------------------------------------------------------------------------------------------------------------------------
def custom_background(window):
        # first level canvas.
        allwidgets = window.grid_slaves(0,0)[0].grid_slaves() + window.grid_slaves(0,0)[0].place_slaves()
        widgets_alphalow = [ widget for widget in allwidgets if widget.winfo_class() == 'Canvas']
        widgets_alphahigh = []
        # sub-level canvas.
        for side in ["Srv", "Clt"]:
                widgets_alphahigh.append(window.pagewidgets[side]["BtnWin"])
                for position in ["Left", "Right"]:
                        widgets_alphahigh.append(window.pagewidgets[side]["AniWin"][position])
                for pagename in window.pagewidgets[side]["PageWin"].keys():
                        widgets_alphalow.append(window.pagewidgets[side]["PageWin"][pagename])
        
        try:
                from PIL import Image, ImageTk

                # Open Image.
                img = Image.open(os.path.dirname(os.path.abspath( __file__ )) + "/graphics/pykms_Keys.gif")
                img = img.convert('RGBA')
                # Resize image.
                img.resize((window.winfo_width(), window.winfo_height()), Image.ANTIALIAS)
                # Put semi-transparent background chunks.
                window.backcrops_alphalow, window.backcrops_alphahigh = ([] for _ in range(2))

                def cutter(master, image, widgets, crops, alpha):
                        for widget in widgets:
                                x, y, w, h = master.get_position(widget)
                                cropped = image.crop((x, y, x + w, y + h))
                                cropped.putalpha(alpha)
                                crops.append(ImageTk.PhotoImage(cropped))
                        # Not in same loop to prevent reference garbage.
                        for crop, widget in zip(crops, widgets):
                                widget.create_image(1, 1, image = crop, anchor = 'nw')

                cutter(window, img, widgets_alphalow, window.backcrops_alphalow, 36)
                cutter(window, img, widgets_alphahigh, window.backcrops_alphahigh, 96)
                        
                # Put semi-transparent background overall.
                img.putalpha(128)
                window.backimg = ImageTk.PhotoImage(img)
                window.masterwin.create_image(1, 1, image = window.backimg, anchor = 'nw')
                
        except ImportError:
                for widget in widgets_alphalow + widgets_alphahigh:
                        widget.configure(background = window.customcolors['lavender'])

        # Hide client.
        window.clt_on_show(force_remove = True)
        # Show Gui.
        window.deiconify()

##-----------------------------------------------------------------------------------------------------------------------------------------------------------
class Animation(object):
        def __init__(self, gifpath, master, widget, loop = False):
                from PIL import Image, ImageTk, ImageSequence

                self.master = master
                self.widget = widget
                self.loop = loop
                self.cancelid = None
                self.flagstop = False
                self.index = 0
                self.frames = []

                img = Image.open(gifpath)
                size = img.size
                for frame in ImageSequence.Iterator(img):
                        static_img = ImageTk.PhotoImage(frame.convert('RGBA'))
                        try:
                                static_img.delay = int(frame.info['duration'])
                        except KeyError:
                                static_img.delay = 100
                        self.frames.append(static_img)

                self.widget.configure(width = size[0], height = size[1])
                self.initialize()

        def initialize(self):
                self.widget.configure(image = self.frames[0])
                self.widget.image = self.frames[0]

        def deanimate(self):
                while not self.flagstop:
                        pass
                self.flagstop = False
                self.index = 0
                self.widget.configure(relief = "raised")

        def animate(self):
                frame = self.frames[self.index]
                self.widget.configure(image = frame, relief = "sunken")
                self.index += 1
                self.cancelid = self.master.after(frame.delay, self.animate)
                if self.index == len(self.frames):
                        if self.loop:
                                self.index = 0
                        else:
                                self.stop()

        def start(self, event = None):
                if str(self.widget['state']) != 'disabled':
                        if self.cancelid is None:
                                if not self.loop:
                                        self.btnani_thread = threading.Thread(target = self.deanimate, name = "Thread-BtnAni")
                                        self.btnani_thread.setDaemon(True)
                                        self.btnani_thread.start()
                                self.cancelid = self.master.after(self.frames[0].delay, self.animate)

        def stop(self, event = None):
                if self.cancelid:
                        self.master.after_cancel(self.cancelid)
                        self.cancelid = None
                        self.flagstop = True
                        self.initialize()


def custom_pages(window, side):
        buttons = window.pagewidgets[side]["BtnAni"]
        labels = window.pagewidgets[side]["LblAni"]
        
        for position in buttons.keys():
                buttons[position].config(anchor = "center",
                                         font = window.customfonts['btn'],
                                         background = window.customcolors['white'],
                                         activebackground = window.customcolors['white'],
                                         borderwidth = 2)

                try:
                        anibtn = Animation(os.path.dirname(os.path.abspath( __file__ )) + "/graphics/pykms_Keyhole_%s.gif" %position,
                                           window, buttons[position], loop = False)
                        anilbl = Animation(os.path.dirname(os.path.abspath( __file__ )) + "/graphics/pykms_Arrow_%s.gif" %position,
                                           window, labels[position], loop = True)

                        def animationwait(master, button, btn_animation, lbl_animation):
                                while btn_animation.cancelid:
                                        pass
                                sleep(1)
                                x, y = master.winfo_pointerxy()
                                if master.winfo_containing(x, y) == button:
                                        lbl_animation.start()

                        def animationcombo(master, button, btn_animation, lbl_animation):
                                wait_thread = threading.Thread(target = animationwait,
                                                               args = (master, button, btn_animation, lbl_animation),
                                                               name = "Thread-WaitAni")
                                wait_thread.setDaemon(True)
                                wait_thread.start()
                                lbl_animation.stop()
                                btn_animation.start()

                        buttons[position].bind("<ButtonPress>", lambda event, anim1 = anibtn, anim2 = anilbl,
                                               bt = buttons[position], win = window:
                                               animationcombo(win, bt, anim1, anim2))
                        buttons[position].bind("<Enter>", anilbl.start)
                        buttons[position].bind("<Leave>", anilbl.stop)

                except ImportError:
                        buttons[position].config(activebackground = window.customcolors['blue'],
                                                 foreground = window.customcolors['blue'])
                        labels[position].config(background = window.customcolors['lavender'])

                        if position == "Left":
                                buttons[position].config(text = '<<')
                        elif position == "Right":
                                buttons[position].config(text = '>>')

##-----------------------------------------------------------------------------------------------------------------------------------------------------------
class ListboxOfRadiobuttons(tk.Frame):
        def __init__(self, master, radios, font, changed, **kwargs):
                tk.Frame.__init__(self, master)

                self.master = master
                self.radios = radios
                self.font = font
                self.changed = changed

                self.scrollv = tk.Scrollbar(self, orient = "vertical")
                self.textbox = tk.Text(self, yscrollcommand = self.scrollv.set, **kwargs)
                self.scrollv.config(command = self.textbox.yview)
                # layout.
                self.scrollv.pack(side = "right", fill = "y")
                self.textbox.pack(side = "left", fill = "both", expand = True)
                # create radiobuttons.
                self.radiovar = tk.StringVar()
                self.radiovar.set('FILE')
                self.create()

        def create(self):
                self.rdbtns = []
                for n, nameradio in enumerate(self.radios):
                        rdbtn = tk.Radiobutton(self, text = nameradio, value = nameradio, variable = self.radiovar,
                                               font = self.font, indicatoron = 0, width = 15,
                                               borderwidth = 3, selectcolor = 'yellow', command = self.change)
                        self.textbox.window_create("end", window = rdbtn)
                        # to force one checkbox per line
                        if n != len(self.radios) - 1:
                                self.textbox.insert("end", "\n")
                        self.rdbtns.append(rdbtn)
                self.textbox.configure(state = "disabled")

        def change(self):
                st = self.state()
                for widget, default in self.changed:
                        wclass = widget.winfo_class()
                        if st in ['STDOUT', 'FILEOFF']:
                                if wclass == 'Entry':
                                        widget.delete(0, 'end')
                                        widget.configure(state = "disabled")
                                elif wclass == 'TCombobox':
                                        if st == 'STDOUT':
                                                widget.set(default)
                                                widget.configure(state = "readonly")
                                        elif st == 'FILEOFF':
                                                widget.set('')
                                                widget.configure(state = "disabled")
                        elif st in ['FILE', 'FILESTDOUT', 'STDOUTOFF']:
                                if wclass == 'Entry':
                                        widget.configure(state = "normal")
                                        widget.delete(0, 'end')
                                        widget.insert('end', default)
                                        widget.xview_moveto(1)
                                elif wclass == 'TCombobox':
                                        widget.configure(state = "readonly")
                                        widget.set(default)
                                elif wclass == 'Button':
                                        widget.configure(state = "normal")

        def configure(self, state):
                for rb in self.rdbtns:
                        rb.configure(state = state)

        def state(self):
                return self.radiovar.get()
