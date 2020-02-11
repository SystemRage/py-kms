#!/usr/bin/env python3

import os
import re
import sys
from collections import Counter

try:
        # Python 2.x imports
        import Tkinter as tk
        import ttk
        import tkFont
except ImportError:
        # Python 3.x imports
        import tkinter as tk
        from tkinter import ttk
        import tkinter.font as tkFont
                        
from pykms_Format import MsgMap, unshell_message, unformat_message

#---------------------------------------------------------------------------------------------------------------------------------------------------------

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

##--------------------------------------------------------------------------------------------------------------------------------------------------------
# https://stackoverflow.com/questions/2914603/segmentation-fault-while-redirecting-sys-stdout-to-tkinter-text-widget
# https://stackoverflow.com/questions/7217715/threadsafe-printing-across-multiple-processes-python-2-x
# https://stackoverflow.com/questions/3029816/how-do-i-get-a-thread-safe-print-in-python-2-6
# https://stackoverflow.com/questions/20303291/issue-with-redirecting-stdout-to-tkinter-text-widget-with-threads
                                
class TextRedirect(object):
        class StdoutRedirect(object):
                tag_num = 0

                grpmsg = unformat_message([MsgMap[1], MsgMap[7], MsgMap[12], MsgMap[20]])
                arrows = [ item[0] for item in grpmsg  ]
                clt_msg_nonewline = [ item[1] for item in grpmsg ]
                arrows = list(set(arrows))
                lenarrow = len(arrows[0])
                srv_msg_nonewline = [ item[0] for item in unformat_message([MsgMap[2], MsgMap[5], MsgMap[13], MsgMap[18]]) ]
                terminator = unformat_message([MsgMap[21]])[0][0]
                msg_align = [ msg[0].replace('\t', '').replace('\n', '') for msg in unformat_message([MsgMap[-2], MsgMap[-4]])]
                newlinecut = [-1, -2, -4, -5]

                def __init__(self, srv_text_space, clt_text_space, customcolors, str_to_print, where):
                        self.srv_text_space = srv_text_space
                        self.clt_text_space = clt_text_space
                        self.customcolors = customcolors
                        self.str_to_print = str_to_print
                        self.where = where
                        self.textbox_do()

                def textbox_finish(self, message):
                        if message == self.terminator:
                                TextRedirect.StdoutRedirect.tag_num = 0
                                TextRedirect.StdoutRedirect.newlinecut = [-1, -2, -4, -5]
                            
                def textbox_write(self, tag, message, color, extras):
                        widget = self.textbox_choose(message)
                        self.w_maxpix, self.h_maxpix = widget.winfo_width(), widget.winfo_height()
                        self.xfont = tkFont.Font(font = widget['font'])
                        widget.configure(state = 'normal')
                        widget.insert('end', self.textbox_format(message), tag)
                        self.textbox_color(tag, widget, color, self.customcolors['black'], extras)
                        widget.after(100, widget.see('end'))
                        widget.configure(state = 'disabled')
                        self.textbox_finish(message)
                                                                                                                                     
                def textbox_choose(self, message):
                        if self.where == "srv":
                                self.srv_text_space.focus_set()
                                return self.srv_text_space
                        elif self.where == "clt":
                                self.clt_text_space.focus_set()
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
                                        message = '\n' * (len(message) - len(msg_strip) + TextRedirect.StdoutRedirect.newlinecut[0]) + msg_strip
                                        TextRedirect.StdoutRedirect.newlinecut.pop(0)

                        count = Counter(message)
                        countab = (count['\t'] if count['\t'] != 0 else 1)
                        message = message.replace('\t' * countab, ' ' * lung)
                        return message

                def textbox_do(self):
                        msgs, TextRedirect.StdoutRedirect.tag_num = unshell_message(self.str_to_print, TextRedirect.StdoutRedirect.tag_num)
                        for tag in msgs:
                                self.textbox_write(tag, msgs[tag]['text'], self.customcolors[msgs[tag]['color']], msgs[tag]['extra'])
                                
        class StderrRedirect(StdoutRedirect):                
                def __init__(self, srv_text_space, clt_text_space, customcolors):
                        self.srv_text_space = srv_text_space
                        self.clt_text_space = clt_text_space
                        self.customcolors = customcolors
                        self.tag_err = 'STDERR'
                        self.xfont = tkFont.Font(font = self.srv_text_space['font'])
                                                
                def write(self, string):
                        self.textbox_color(self.tag_err, self.srv_text_space, self.customcolors['red'], self.customcolors['black'])
                        self.srv_text_space.configure(state = 'normal')
                        self.srv_text_space.insert('end', string, self.tag_err)
                        self.srv_text_space.see('end')
                        self.srv_text_space.configure(state = 'disabled')
                
##-------------------------------------------------------------------------------------------------------------------------------------------------------
class TextDoubleScroll(tk.Frame): 
        def __init__(self, master, **kwargs):
                """ Initialize.
                        - horizontal scrollbar
                        - vertical scrollbar
                        - text widget
                """
                self.master = master
                tk.Frame.__init__(self, master)
                
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

##--------------------------------------------------------------------------------------------------------------------------------------------------
def custom_background(window):
        allwidgets = window.grid_slaves(0,0)[0].grid_slaves() + window.grid_slaves(0,0)[0].place_slaves()
        widgets = [ widget for widget in allwidgets if widget.winfo_class() == 'Canvas']
        
        try:
                from PIL import Image, ImageTk

                # Open Image.
                img = Image.open(os.path.dirname(os.path.abspath( __file__ )) + "/pykms_Keys.gif")
                # Resize image.
                img.resize((window.winfo_width(), window.winfo_height()), Image.ANTIALIAS)
                # Put semi-transparent background chunks.
                window.backcrops = []
                   
                for widget in widgets:
                        x, y, w, h = window.get_position(widget)
                        cropped = img.crop((x, y, x + w, y + h))
                        cropped.putalpha(24)
                        window.backcrops.append(ImageTk.PhotoImage(cropped))
                                
                # Not in same loop to prevent reference garbage.
                for crop, widget in zip(window.backcrops, widgets):
                        widget.create_image(1, 1, image = crop, anchor = 'nw')
                        
                # Put semi-transparent background overall.
                img.putalpha(96)
                window.backimg = ImageTk.PhotoImage(img)
                window.masterwin.create_image(1, 1, image = window.backimg, anchor = 'nw')
                
        except ImportError:
                for widget in widgets:
                        widget.configure(background = window.customcolors['lavender'])

        # Hide client.
        window.clt_on_show(force = True)
        # Show Gui.
        window.deiconify()
        
##---------------------------------------------------------------------------------------------------------------------------------------------------------
