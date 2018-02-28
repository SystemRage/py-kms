#!/usr/bin/env python

import sys

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


class ShellStyle(object):
    def style(self, s, style):
        return style + s + '\033[0m'

    def green(self, s):
        return self.style(s, '\033[92m')

    def blue(self, s):
        return self.style(s, '\033[94m')

    def yellow(self, s):
        return self.style(s, '\033[93m')

    def red(self, s):
        return self.style(s, '\033[91m')

    def magenta(self, s):
        return self.style(s, '\033[95m')
    
    def cyan(self, s):
        return self.style(s, '\033[96m')

    def white(self, s):
        return self.style(s, '\033[97m')

    def bold(self, s):
        return self.style(s, '\033[1m')

    def underline(self, s):
        return self.style(s, '\033[4m')




def shell_message(nshell):
     
    shelldict = {0: ShellStyle().yellow("Client generating RPC Bind Request..."),
                 1: ShellStyle().yellow("Client sending RPC Bind Request...") + ShellStyle().red("\t\t\t\t===============>"),
                 2: ShellStyle().red("===============>\t\t") + ShellStyle().yellow("Server received RPC Bind Request !!!"),
                 3: ShellStyle().yellow("\t\t\t\tServer parsing RPC Bind Request..."),
                 4: ShellStyle().yellow("\t\t\t\tServer generating RPC Bind Response..."),
                 5: ShellStyle().red("<===============\t\t") + ShellStyle().yellow("Server sending RPC Bind Response..."),
                 6: ShellStyle().green("\t\t\t\tRPC Bind acknowledged !!!\n"),
                 7: ShellStyle().yellow("Client received RPC Bind Response !!!") + ShellStyle().red("\t\t\t\t<==============="),
                 8: ShellStyle().green("RPC Bind acknowledged !!!\n"),
                 9: ShellStyle().blue("Client generating Activation Request dictionary..."),
                 10: ShellStyle().blue("Client generating Activation Request data..."),
                 11: ShellStyle().blue("Client generating RPC Activation Request..."),
                 12: ShellStyle().blue("Client sending RPC Activation Request...") + ShellStyle().red("\t\t\t===============>"),
                 13: ShellStyle().red("===============>\t\t") + ShellStyle().blue("Server received RPC Activation Request !!!"),
                 14: ShellStyle().blue("\t\t\t\tServer parsing RPC Activation Request..."),
                 15: ShellStyle().blue("\t\t\t\tServer processing KMS Activation Request..."),
                 16: ShellStyle().blue("\t\t\t\tServer processing KMS Activation Response..."),
                 17: ShellStyle().blue("\t\t\t\tServer generating RPC Activation Response..."),
                 18: ShellStyle().red("<===============\t\t") + ShellStyle().blue("Server sending RPC Activation Response..."),
                 19: ShellStyle().green("\t\t\t\tServer responded, now in Stand by...\n"),
                 20: ShellStyle().blue("Client received Response !!!") + ShellStyle().red("\t\t\t\t\t<==============="),
                 21: ShellStyle().green("Activation Done !!!"),
                 -1: ShellStyle().red("\t\t\t\t\t\t\t\tServer receiving"),
                 -2: ShellStyle().red("Client sending"),
                 -3: ShellStyle().red("Client receiving"),
                 -4: ShellStyle().red("\t\t\t\t\t\t\t\tServer sending")
                 }
        
    if isinstance(nshell, list):
        for n in nshell:
            print shelldict[n]
    else:
        print shelldict[nshell]


             

