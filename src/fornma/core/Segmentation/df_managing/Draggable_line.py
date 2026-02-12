# -*- coding: utf-8 -*-
"""
Created on Sun Aug  1 19:29:16 2021

@author: Luiza
"""

import matplotlib.lines as lines

line_coord_list = [] 
class draggable_lines:
    def __init__(self, ax, kind, XorY):
        self.ax = ax
        self.c = ax.get_figure().canvas
        self.o = kind
        self.XorY = XorY
        self.line0 = 0
       

        if kind == "h":
            x = [-100, 100]
            y = [XorY, XorY]

        elif kind == "v":
            x = [XorY, XorY]
            y = [-100000, 100000]
        self.line = lines.Line2D(x, y, picker=5)
        self.ax.add_line(self.line)
        self.c.draw_idle()
        self.sid = self.c.mpl_connect('pick_event', self.clickonline)

    def clickonline(self, event):
        if event.artist == self.line:
            line_coord_list.append(event.artist._label)
            self.follower = self.c.mpl_connect("motion_notify_event", self.followmouse)
            self.releaser = self.c.mpl_connect("button_press_event", self.releaseonclick)
            
    def followmouse(self, event):
        if self.o == "h":
            self.line.set_ydata([event.ydata, event.ydata])
        else:
            self.line.set_xdata([event.xdata, event.xdata])
        self.c.draw_idle()

    def releaseonclick(self, event):
        if self.o == "h":
            self.XorY = self.line.get_ydata()[0]
        else:
            self.XorY = self.line.get_xdata()[0]

    
        line_coord_list.append(self.XorY)
        self.c.mpl_disconnect(self.releaser)
        self.c.mpl_disconnect(self.follower)
     

 