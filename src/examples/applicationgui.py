#!/usr/bin/env python

import wx,os, signal

 
class MainWindow(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self,parent,id, title):
        wx.Frame.__init__(self,parent,wx.ID_ANY,title,size=(200,100))
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.b1 = wx.Button(self, -1, "CC1K Pinger")
        self.Bind(wx.EVT_BUTTON, self.OnBCC1KPing, self.b1)
        self.buttonSizer.Add(self.b1, 1, wx.EXPAND)
        self.b2 = wx.Button(self, -1, "CC1K Ponger")
        self.Bind(wx.EVT_BUTTON, self.OnBCC1KPong, self.b2)
        self.buttonSizer.Add(self.b2, 1, wx.EXPAND)
        self.b3 = wx.Button(self, -1, "CC2420 Pinger")
        self.Bind(wx.EVT_BUTTON, self.OnBCC2420Ping, self.b3)
        self.buttonSizer.Add(self.b3, 1, wx.EXPAND)
        self.b4 = wx.Button(self, -1, "CC2420 Ponger")
        self.Bind(wx.EVT_BUTTON, self.OnBCC2420Pong, self.b4)
        self.buttonSizer.Add(self.b4, 1, wx.EXPAND)
        self.b5 = wx.Button(self, -1, "CC1K To CC2420")
        self.Bind(wx.EVT_BUTTON, self.OnBCC1KCC2420, self.b5)
        self.buttonSizer.Add(self.b5, 1, wx.EXPAND)

        self.sizer.Add(self.buttonSizer, 0, wx.EXPAND)
        self.control = wx.TextCtrl(self,1,style=wx.TE_MULTILINE)
        self.sizer.Add(self.control, 1, wx.EXPAND)
        self.Show(True)
        self.cpid = -1
        
    def OnBCC1KPing(self, evt):
        self.control.AppendText("Starting CC1K Pinger\n")
        print self.cpid
        if self.cpid > 0:
            os.kill(self.cpid, signal.SIGKILL)
        self.cpid = os.spawnl(os.P_NOWAIT, "cc1k_pinger.py")
        
    def OnBCC1KPong(self, evt):
        self.control.AppendText("Starting CC1K Ponger\n")
        print self.cpid
        if self.cpid > 0:
            os.kill(self.cpid, signal.SIGKILL)
        self.cpid = os.spawnl(os.P_NOWAIT, "cc1k_ponger.py")
    def OnBCC2420Ping(self, evt):
        pass
    def OnBCC2420Pong(self, evt):
        pass
    def OnBCC1KCC2420(self, evt):
        pass

app = wx.PySimpleApp()
frame=MainWindow(None,-1,'SDR Applications Demo')
app.MainLoop()
