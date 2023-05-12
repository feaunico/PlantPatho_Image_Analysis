#############################################################################
#                                                                           #
###### Image analyse for fungal cultures and necrosis on plant leaves #######
#                                                                           #
#############################################################################

import numpy as np
import matplotlib.pyplot as plt
import os.path
from matplotlib.widgets import LassoSelector, RectangleSelector, EllipseSelector
from pylab import *

from matplotlib import path
from PIL import Image, ImageChops
import wx, os, os.path, random, matplotlib, glob
from matplotlib.patches import Ellipse
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.patches as patches
from sklearn import svm
from sklearn.externals import joblib

from skimage import data, color, io
from skimage.transform import hough_circle, hough_circle_peaks
from skimage.feature import canny

from datetime import datetime
from datetime import date



######################################################################
#########   BETA TO TEST and USE
######################################################################

        # acquire a lock on the widget drawing
        #self.canvas.widgetlock(self.lasso)


        #self.canvas.widgetlock.release(self.lasso)
        #del self.lasso

ID_OPEN, ID_ELLIPSE, ID_RECTANGLE, ID_LASSO, ID_CORRECT, ID_FILL, ID_LOUPE, ID_SAVE, ID_BACK = 1, 2, 3, 4, 5, 6, 7, 8, 9




def countpix(A):
    _A_ = A.flatten()
    nb = 0
    for entr in _A_:
        if entr <= 1.0:

            nb = nb + 1
    print 'voici nb', nb
    return nb


def interpret_rectangle_4_res(data,x1,y1,x2,y2):
    tls, dd = [], []
    for x in data:
        ls = []
        for y in x:
            ls.append("(" + str(y[0]) + ',' + str(y[1]) + ',' + str(y[2])+ ")")
        dd.append(ls)
    print x1,y1,x2,y2
    i = 0
    allls = []
    while i < len(data):
        if i > y1 and i <= y2:
            j = 0
            nls = []
            while j < len(data[0]):
                if j > x1 and j <= x2:
                    nls.append(data[i][j].tolist())
                j = j + 1
            allls.append(nls)
        i = i + 1
    return allls

def interpret_ellipse_4_res(data,x1,y1,x2,y2):
    tls, dd = [],[]
    for x in data:
        ls = []
        for y in x:
            ls.append("(" + str(y[0]) + ',' + str(y[1]) + ',' + str(y[2])+ ")")
        dd.append(ls)
    x = round((float(x2 - x1)/2 ) + x1)
    y = round((float(y2 - y1)/2 ) + y1)
    tpl = data.tolist()
    y_int = np.arange(0, len(tpl))
    x_int = np.arange(0, len(tpl[0]))
    ellipse = Ellipse(xy=(x,y), width=x2-x1, height=y2-y1, angle=0)
    g = np.meshgrid(x_int, y_int)

    coords = list(zip(*(c.flat for c in g)))
    ellipse_left, ellipse_right, ellipse_top, ellipse_bottom   = round(x - float((x2-x1))/2),  round(x + float((x2-x1))/2), round(y + float((y2-y1))/2), round(y - float((y2-y1))/2)
    ellipsepoints = []

    print ellipse
    print ellipse_left, ellipse_right, ellipse_top, ellipse_bottom
    lspixels = []

    for p in coords:

        if p[0] >= ellipse_left and  p[0] <= ellipse_right :

            if p[1] <= ellipse_top and p[1] >= ellipse_bottom:
                ellipsepoints.append(p)
                if ellipse.contains_point(p, radius=0):

                    lspixels.append(data[p[1]][p[0]].tolist())
                else:
                    lspixels.append([255, 255, 255])


    #for x,y in zip(ellipsepoints,lspixels):
    #    print x, y

    uq = []
    for x in ellipsepoints:
        if x[1] not in uq:
            uq.append(x[1])
    allls = []
    for x in uq:
        nls = []
        tag = 0
        for y,z in zip(ellipsepoints,lspixels):
            if y[1] == x:
                tag =1
                nls.append(z)
            else:
                if tag == 1:
                    allls.append(nls)
                    tag = 0
    return allls





def interpret_rectangle(data,_array_,x1,y1,x2,y2,_cl_):
    dcnb = {0:4,1:1,2:8,3:3}
    tls, dd = [],[]
    for x in data:
        ls = []
        for y in x:
            ls.append("(" + str(y[0]) + ',' + str(y[1]) + ',' + str(y[2])+ ")")
        dd.append(ls)
    i = 0
    while i < len(_array_):
        print i
        j = 0
        ssls = []
        while j < len(_array_[0]):
            if i >= y1 and i <= y2 and j >= x1 and j <= x2:
                tls.append(dd[i][j])
                _array_[i][j] = dcnb[_cl_]
            else:
                if _array_[i][j] not in [4,1,8,3]:
                    _array_[i][j] = np.nan
            j = j + 1
        i = i + 1
    return tls, _array_

def interpret_ellipse(data,_array_,x1,y1,x2,y2,_cl_):
    print 'you are in ellipse'
    dcnb = {0:4,1:1,2:8,3:3}
    tls, dd = [],[]
    for x in data:
        ls = []
        for y in x:
            ls.append("(" + str(y[0]) + ',' + str(y[1]) + ',' + str(y[2])+ ")")
        dd.append(ls)
    x = round((float(x2 - x1)/2 ) + x1)
    y = round((float(y2 - y1)/2 ) + y1)
    tpl = _array_.tolist()
    y_int = np.arange(0, len(tpl))
    x_int = np.arange(0, len(tpl[0]))
    ellipse = Ellipse(xy=(x,y), width=x2-x1, height=y2-y1, angle=0)
    g = np.meshgrid(x_int, y_int)
    coords = list(zip(*(c.flat for c in g)))
    ellipse_left, ellipse_right, ellipse_top, ellipse_bottom   = round(x - float((x2-x1))/2),  round(x + float((x2-x1))/2), round(y + float((y2-y1))/2), round(y - float((y2-y1))/2)
    ellipsepoints = []
    for p in coords:
        if p[0] >= ellipse_left and  p[0] <= ellipse_right and p[1] <= ellipse_top and p[1] >= ellipse_bottom:
            if ellipse.contains_point(p, radius=0):
                ellipsepoints.append(p)
    for x in ellipsepoints:
        _array_[x[1]][x[0]] = dcnb[_cl_]
        tls.append(dd[x[1]][x[0]])
    return tls, _array_





def updateArray(array, indices, cl):
    lin = np.arange(array.size)
    nArray = array.flatten()
    newArray = []
    for x in nArray:
        if x == 0.0:
            newArray.append(np.nan)
        else:
            newArray.append(x)
    newArray = np.asarray(newArray)
    if cl == 0:        newArray[lin[indices]] = 4
    if cl == 1:        newArray[lin[indices]] = 1
    if cl == 2:        newArray[lin[indices]] = 8
    if cl == 3:        newArray[lin[indices]] = 3
    if cl == 4:        newArray[lin[indices]] = np.nan
    if cl == 5:        newArray[lin[indices]] = 0.5
    if cl == 6:        newArray[lin[indices]] = 0.75
    return newArray.reshape(array.shape)





def retourne(array):
    fnl = []
    i = 0
    while i < len(array[0]):
        ls = []
        for x in array:
            ls.append(x[i])
        fnl.append(ls)
        i = i + 1
    return fnl


def cleanselection(array):
    ls = []
    for x in array:
        tag = 0
        for y in x:
            if y.tolist() != [0,0,0]:
                tag = 1
        if tag == 1:
            ls.append(x.tolist())
    i = 0
    fnl = []
    while i < len(ls[0]):
        tag = 0
        lss = []
        for x in ls:
            if x[i] == [0, 0, 0]:
                lss.append([255, 255, 255])
                #lss.append([np.nan, np.nan, np.nan])
            else:
                lss.append(x[i])
            if x[i] != [0, 0, 0]:
                tag = 1
        if tag == 1:
            fnl.append(lss)
        i = i + 1
    return fnl




class MyGUIApp(wx.App):
    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        try:os.mkdir('my_images_out')
        except:pass
        now = datetime.now()
        current_time = now.strftime("%H_%M_%S")
        today = date.today()
        current_date = today.strftime("%d_%m_%Y")
        self.datapoint = current_date + '_' + current_time
        self.frame = wx.Frame(None, title='MyGUIApp v0.2')
        self.panel = wx.Panel(self.frame)
        self.EllipseSel, self.RectangleSel, self.LassoSel  = 0, 0, 1
        self.val = ()
        self.w, self.h = wx.DisplaySize()
        self.scaled, self.ran, self.op = 0, 0, 0

        #build drawing canvas
        self.fig = plt.figure(figsize=(float(self.w)/100, float(self.h)/100))
        self.ax1 = plt.subplot2grid((3, 2), (0, 0),rowspan=2)
        self.ax1.set_xticks([])
        self.ax1.set_yticks([])
        self.ax1.plot()
        self.ax2 = plt.subplot2grid((3, 2), (0, 1),rowspan=2)
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.plot()
        self.ax3 = plt.subplot2grid((3, 2), (2, 0))
        self.ax3.set_xlim(0,1)
        self.ax3.set_ylim(0,1)
        self.ax3.plot()
        self.ax3.axis('off')
        self.ax4 = plt.subplot2grid((3, 2), (2, 1))
        self.ax4.axis('off')
        self.ax4.set_xlim(0,1)
        self.ax4.set_ylim(0,1)
        self.ax4.plot()
        self.canvas = FigureCanvas(self.panel, -1,self.fig)
        self.canvas.draw_idle()
        self.openEvent(self)

        #add menu bar
        self.createMenus()
        self.connectItemsWithEvents()
        self.frame.SetMenuBar(self.menuBar)
        self.StatusBar = self.frame.CreateStatusBar(1)

        #add toolbar
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        toolbar1 = wx.ToolBar(self.panel)

        open = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/open.jpg'), id=ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.openEvent, id=ID_OPEN)
        open.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterOpen)
        open.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        rectangle = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/rectangle.jpg'),id=ID_RECTANGLE)
        self.Bind(wx.EVT_BUTTON, self.selectRectangle, id=ID_RECTANGLE)
        rectangle.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterRectangle)
        rectangle.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        ellipse = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/ellipse.jpg'), id= ID_ELLIPSE)
        self.Bind(wx.EVT_BUTTON, self.selectEllipse, id=ID_ELLIPSE)
        ellipse.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterEllipse)
        ellipse.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        lasso = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/lasso2.jpg'),id=ID_LASSO)
        self.Bind(wx.EVT_BUTTON, self.selectLasso, id=ID_LASSO)
        lasso.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterLasso)
        lasso.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        save = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/save.jpg'), id=ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.saveit, id=ID_SAVE)
        save.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterSave)
        save.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        brush = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/erase.jpg'), id=ID_CORRECT)
        self.Bind(wx.EVT_BUTTON, self.erase_selection, id=ID_CORRECT)
        brush.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterAdd)
        brush.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        spray = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/bucket.jpg'), id= ID_FILL)
        self.Bind(wx.EVT_BUTTON, self.fill_selection, id=ID_FILL)
        spray.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterErase)
        spray.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)


        loupe = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/loupe.jpg'), id= ID_LOUPE)
        self.Bind(wx.EVT_BUTTON, self.loupe_selection, id=ID_LOUPE)
        loupe.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterErase)
        loupe.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        back = wx.BitmapButton(toolbar1, bitmap=wx.Bitmap('icons/back.jpg'), id= ID_BACK)
        self.Bind(wx.EVT_BUTTON, self.back_to_original, id=ID_BACK)
        back.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterErase)
        back.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)





        toolbar1.SetToolBitmapSize((31, 31))

        hbox1.Add(open)
        hbox1.Add(save)
        lbl = wx.StaticText(toolbar1)
        lbl.SetLabel("       ")
        hbox1.Add(lbl)
        hbox1.Add(rectangle)
        hbox1.Add(ellipse)
        hbox1.Add(lasso)
        lbl = wx.StaticText(toolbar1)
        lbl.SetLabel("       ")
        hbox1.Add(lbl)
        hbox1.Add(brush)
        hbox1.Add(spray)
        lbl = wx.StaticText(toolbar1)
        lbl.SetLabel("       ")
        hbox1.Add(lbl)
        hbox1.Add(loupe)
        hbox1.Add(back)
        toolbar1.SetSizer(hbox1)
        vbox.Add(toolbar1, 0, wx.EXPAND)
        vbox.Add(self.canvas, 0, wx.EXPAND)
        self.panel.SetSizer(vbox)
        toolbar1.Realize()
        plt.tight_layout()

        #show main frame
        self.frame.Show()

    def connectItemsWithEvents(self) :
        self.Bind(wx.EVT_MENU, self.openEvent, self.openItem)
        self.Bind(wx.EVT_MENU, self.clearEvent, self.clearItem)
        self.Bind(wx.EVT_MENU, self.reinit_selectclassEvent, self.selectItem)
        self.Bind(wx.EVT_MENU, self.trainEvent, self.trainItem)
        self.Bind(wx.EVT_MENU, self.runFEvent, self.runItemF)
        self.Bind(wx.EVT_MENU, self.runSEvent, self.runItemS)
        self.Bind(wx.EVT_MENU, self.scaleEvent, self.scaleItem)
        self.Bind(wx.EVT_MENU, self.autoscalepetri,self.autoscaleItem)

    def createMenus(self) :
        self.menuBar = wx.MenuBar()
        self.menuFile = wx.Menu()
        self.menuBar.Append(self.menuFile, '&File')
        self.openItem = wx.MenuItem(self.menuFile, wx.NewId(), u'&open ...\tCTRL+O')
        self.menuFile.Append(self.openItem)
        self.clearItem = wx.MenuItem(self.menuFile, wx.NewId(), '&clear\tCTRL+C')
        self.menuFile.Append(self.clearItem)
        self.menuEdit = wx.Menu()
        self.menuBar.Append(self.menuEdit, '&Training')
        self.selectItem = wx.MenuItem(self.menuEdit, wx.NewId(), u'&select classes ...\tCTRL+S')
        self.menuEdit.Append(self.selectItem)
        self.trainItem = wx.MenuItem(self.menuEdit, wx.NewId(), u'&train model...\tCTRL+T')
        self.menuEdit.Append(self.trainItem)
        self.menuRunning = wx.Menu()
        self.menuBar.Append(self.menuRunning, '&Running')
        self.runItemF = wx.MenuItem(self.menuRunning, wx.NewId(), u'&run full...\tCTRL+R')
        self.menuRunning.Append(self.runItemF)
        self.runItemS = wx.MenuItem(self.menuRunning, wx.NewId(), u'&run sel...\tCTRL+R+S')
        self.menuRunning.Append(self.runItemS)
        self.menuScaling = wx.Menu()
        self.menuBar.Append(self.menuScaling, '&Scale')
        self.scaleItem = wx.MenuItem(self.menuScaling, wx.NewId(), u'&Define scale')
        self.menuScaling.Append(self.scaleItem)
        self.autoscaleItem = wx.MenuItem(self.menuScaling, wx.NewId(), u'&Auto scale Petri')
        self.menuScaling.Append(self.autoscaleItem)


    def OnMouseEnterOpen(self,event):
        self.StatusBar.SetStatusText("Open image")
        event.Skip()

    def OnMouseEnterSave(self,event):
        self.StatusBar.SetStatusText("Save output")
        event.Skip()

    def OnMouseEnterRectangle(self,event):
        self.StatusBar.SetStatusText("Rectangle selection")
        event.Skip()

    def OnMouseEnterLasso(self,event):
        self.StatusBar.SetStatusText("Lasso selection")
        event.Skip()

    def OnMouseEnterEllipse(self,event):
        self.StatusBar.SetStatusText("Ellipse selection")
        event.Skip()

    def OnMouseEnterErase(self,event):
        self.StatusBar.SetStatusText("Erase pixels")
        event.Skip()

    def OnMouseEnterAdd(self,event):
        self.StatusBar.SetStatusText("Add pixels")
        event.Skip()

    def OnMouseLeave(self, event):
        self.StatusBar.SetStatusText("")
        event.Skip()

    def selectEllipse(self,event):
        print 'ellipse voici self.val', self.val
        self.EllipseSel, self.RectangleSel, self.LassoSel = 1, 0, 0
        self.pic_tool()

        print 'ellipse selected'

    def selectRectangle(self,event):
        print 'rectangle'
        self.EllipseSel, self.RectangleSel, self.LassoSel = 0, 1, 0
        #self.selectclassEvent(self)
        print 'rectangle selected'

        self.pic_tool()

    def selectLasso(self,event):
        self.EllipseSel, self.RectangleSel, self.LassoSel = 0, 0, 1
        #self.selectclassEvent(self)
        print 'lasso selected'

        self.pic_tool()

    def reinit_selectclassEvent(self, event):
        if self.ran == 1:
            self.ran = 0
            self.ax4.clear()
            self.ax2.clear()
            self.ax2.axis('off')
            self.ax4.axis('off')
            self.canvas.draw_idle()
        self.val = ()
        self.selectclassEvent(self)

    def selectclassEvent(self, event):
        print 'YOU ARE IN IT', self.val
        if self.val == ():
            dlg = DialogClasses(self.dic_cl_name)
            res = dlg.ShowModal()
            if res == wx.ID_OK:
                self.val = (dlg.rd1.GetValue(), dlg.rd2.GetValue(), dlg.rd3.GetValue(), dlg.rd4.GetValue())
                print dlg.txt1.GetValue(), dlg.txt2.GetValue(), dlg.txt3.GetValue(), dlg.txt4.GetValue()
                if dlg.txt1.GetValue() != 'Necrosis': self.dic_cl_name['cl1'] = dlg.txt1.GetValue()
                if dlg.txt2.GetValue() != 'Leaf': self.dic_cl_name['cl2'] = dlg.txt2.GetValue()
                if dlg.txt3.GetValue() != 'Background': self.dic_cl_name['cl3'] = dlg.txt3.GetValue()
                if dlg.txt4.GetValue() != 'Other': self.dic_cl_name['cl4'] = dlg.txt4.GetValue()
            dlg.Destroy()
        self.running_or_training = 0
        self.pic_tool()


    def pic_tool(self):
        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass

        xv, yv = np.meshgrid(np.arange(len(self.image[0])), np.arange(len(self.image)))
        self.pix = np.vstack((xv.flatten(), yv.flatten())).T
        if self.running_or_training == 0:
            if self.val[0] == True:
                color = 'red'
                self.cl = 0
            if self.val[1] == True:
                color = 'blue'
                self.cl = 1
            if self.val[2] == True:
                color = 'k'
                self.cl = 2
            if self.val[3] == True:
                color = 'green'
                self.cl = 3
        if self.RectangleSel == 1 and self.EllipseSel == 0 and self.LassoSel == 0:
            if self.running_or_training == 0:
                self.StatusBar.SetStatusText("Training - Rectangle selection")
                self.rect = RectangleSelector(self.ax1, self.onselect_rectangle, rectprops = dict( edgecolor = color, fill=False))
                connect('key_press_event', self.rect)
            if self.running_or_training == 1:
                self.StatusBar.SetStatusText("Running - Rectangle selection")
                self.rect = RectangleSelector(self.ax1, self.onselect_rectangle_4_run,rectprops=dict(edgecolor='blue', fill=False))
                connect('key_press_event', self.rect)


        elif self.RectangleSel == 0 and self.EllipseSel == 1 and self.LassoSel == 0:
            if self.running_or_training == 0:
                self.StatusBar.SetStatusText("Training - Ellipse selection")
                self.elip = EllipseSelector(self.ax1, self.onselect_rectangle, rectprops = dict( edgecolor = color, fill=False))
                connect('key_press_event', self.elip)
            if self.running_or_training == 1:
                self.StatusBar.SetStatusText("Running - Ellipse selection")
                self.elip = EllipseSelector(self.ax1, self.onselect_ellipse_4_run, rectprops = dict( edgecolor = 'blue', fill=False))
                connect('key_press_event', self.elip)

        elif self.RectangleSel == 0 and self.EllipseSel == 0 and self.LassoSel == 1:
            if self.running_or_training == 0:
                self.StatusBar.SetStatusText("Training - Lasso selection")
                self.lasso = LassoSelector(self.ax1, self.onselect_lasso, lineprops = {'color':color})
                connect('key_press_event', self.lasso)

            if self.running_or_training == 1:
                self.StatusBar.SetStatusText("Running - Lasso selection")
                self.lasso = LassoSelector(self.ax1, onselect=self.onselect_lasso_run)
                connect('key_press_event', self.lasso)


        self._val_ = (self.val[0],self.val[1],self.val[2],self.val[3])





    def onselect_rectangle(self,eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.data = np.array(self.image)
        if self.RectangleSel == 1 and self.EllipseSel == 0 and self.LassoSel == 0:
            training_ls, self.array = interpret_rectangle(self.data,self.array,x1,y1,x2,y2,self.cl)
        if self.RectangleSel == 0 and self.EllipseSel == 1 and self.LassoSel == 0:
            training_ls, self.array = interpret_ellipse(self.data,self.array,x1,y1,x2,y2,self.cl)
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.imshow(self.image)
        self.ax2.imshow(self.array,cmap='tab10',vmin = 1, vmax = 10, alpha = 0.9)
        self.fig.canvas.draw_idle()

        if self._val_[0] == True:  fx = open('class1_tp','a')
        elif self._val_[1] == True: fx = open('class2_tp','a')
        elif self._val_[2] == True: fx = open('class3_tp','a')
        elif self._val_[3] == True: fx = open('class4_tp','a')
        for x in training_ls:
            fx.write(x+ '\n')
        fx.close()
        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass

        #ICI RUN A NEW DIALOG BOX ASKING IF YOU WANT TO PICK MORE

        if self.val[0] == True:nom = 'Necrosis'
        if self.val[1] == True:nom = 'Leaf'
        if self.val[2] == True:nom = 'Background'
        if self.val[3] == True:nom = 'Other'
        dlg = PickMore(nom)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.selectclassEvent(self)
        else:
            dlg.Close(True)





    def onselect_lasso(self,verts):
        if self.scaled != 0:
            if self.scaled[3] - self.scaled[2] > self.scaled[1] - self.scaled[0]:
                self.ax1.text(self.scaled[0] + 30,(float(self.scaled[3] - self.scaled[2])/2) + self.scaled[2], str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')
            else:
                self.ax1.text((float(self.scaled[1] - self.scaled[0])/2) + self.scaled[0], self.scaled[3] + 20,str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')

            self.ax1.plot((self.scaled[0],self.scaled[1]),(self.scaled[2],self.scaled[3]),'r-')       #self.scaled = (self._dx, self._fx,self._dy,self._fy)
        p = path.Path(verts)
        self.ind = p.contains_points(self.pix, radius=1)
        self.array = updateArray(self.array, self.ind, self.cl)
        #I need that if I want to show what is selected on ax2
        #array = updateArray(self.array, self.ind,self.cl)
        #self.msk.set_data(array)
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.imshow(self.image)
        self.ax2.imshow(self.array,cmap='tab10',vmin = 1, vmax = 10, alpha = 0.9)
        self.fig.canvas.draw_idle()

        self.data = np.array(self.image)
        self.training_ls, dd = [], []
        for x in self.data:
            ls = []
            for y in x:
                ls.append("(" + str(y[0]) + ',' + str(y[1]) + ',' + str(y[2])+ ")")
            dd.append(ls)
        dd = np.array(dd)
        for x,y in zip(self.pix, self.ind) :
            if y == True:
                self.training_ls.append(dd[x[1]][x[0]])
        if self._val_[0] == True:  fx = open('class1_tp','a')
        elif self._val_[1] == True: fx = open('class2_tp','a')
        elif self._val_[2] == True: fx = open('class3_tp','a')
        elif self._val_[3] == True: fx = open('class4_tp','a')
        for x in self.training_ls:
            fx.write(x+ '\n')
        fx.close()
        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass

        if self.val[0] == True:nom = 'Necrosis'
        if self.val[1] == True:nom = 'Leaf'
        if self.val[2] == True:nom = 'Background'
        if self.val[3] == True:nom = 'Other'
        dlg = PickMore(nom)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.selectclassEvent(self)
        else:
            dlg.Close(True)
        # ICI RUN A NEW DIALOG BOX ASKING IF YOU WANT TO PICK MORE

    def trainEvent(self, event):
        self.ran = 0
        # ca permettra de reinitialiser le dictionnaire
        #self.dic_cl_name = {'cl1':'Class 1','cl2':'Class 2','cl3':'Class 3','cl4':'Class 4'}

        dlg = DialogTrain()
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            self.modelname = dlg.comboBox1.GetValue()

            if self.modelname != '' :
                if os.path.isfile("class1_tp") == True:
                    dlg.Destroy()
                    learn = Learning()
                    self.svc = learn.runSVC(self.modelname)
                    print 'learning typE 1 done', self.modelname, 'has been updated'
                    fo = open(self.modelname + '.log')
                    self.mdn = fo.readlines()
                    fo.close()
                    self.dic_cl_name['cl1'] = self.mdn[0].replace('\n','')
                    self.dic_cl_name['cl2'] = self.mdn[1].replace('\n','')
                    self.dic_cl_name['cl3'] = self.mdn[2].replace('\n','')
                    self.dic_cl_name['cl4'] = self.mdn[3].replace('\n','')
                else:
                    dlg.Destroy()
                    self.svc = joblib.load(self.modelname)
                    fo = open(self.modelname + '.log')
                    self.mdn = fo.readlines()
                    fo.close()
                    self.dic_cl_name['cl1'] = self.mdn[0].replace('\n','')
                    self.dic_cl_name['cl2'] = self.mdn[1].replace('\n','')
                    self.dic_cl_name['cl3'] = self.mdn[2].replace('\n','')
                    self.dic_cl_name['cl4'] = self.mdn[3].replace('\n','')
            elif dlg.txt.GetValue() != '' and dlg.txt.GetValue() !=  'Model name':
                if os.path.isfile("class1_tp") == True and os.path.isfile("class2_tp") == True:
                    self.modelname = dlg.txt.GetValue() + '.pkl'
                    dlg.Destroy()
                    learn = Learning()
                    self.svc = learn.runSVC(self.modelname)   #self.scv is the model used in the runPrediction instance
                    print 'learning type 3 done, a new', self.modelname, 'was created'
                    flog = open(self.modelname + '.log','w')
                    flog.write(self.dic_cl_name['cl1']+'\n')
                    flog.write(self.dic_cl_name['cl2']+'\n')
                    flog.write(self.dic_cl_name['cl3']+'\n')
                    flog.write(self.dic_cl_name['cl4']+'\n')
                    flog.close()
                else:
                    dlg = DialogPlease(1,(250, 200))
                    res = dlg.ShowModal()
                    if res == wx.ID_OK:
                        dlg.Destroy()
            else:
                    dlg = DialogPlease(2,(250, 200))
                    res = dlg.ShowModal()
                    if res == wx.ID_OK:
                        dlg.Destroy()
            self.ax3.clear()
            self.ax3.set_xlim(0,1)
            self.ax3.set_ylim(0,1)
            self.ax3.axis('off')
            self.ax3.text(0.05,0.7,'Image file : ' + str(os.path.split(self.filename)[-1]))
            try:
                self.ax3.text(0.05,0.5,'Model selected : ' + str(self.modelname.replace('.pkl','')))
            except:
                self.ax3.text(0.05,0.5,'No active model')
            if self.scaled != 0:
                self.ax3.text(0.05,0.3,'Image scaled')
            self.canvas.draw_idle()

    def scaleEvent(self, event):
        self.click = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.release = self.fig.canvas.mpl_connect('button_release_event', self.onrelease)

    def onclick(self,event):
        self.StatusBar.SetStatusText("Scaling")
        self.ax1.clear()
        self.ax1.set_yticks([])
        self.ax1.set_xticks([])
        self.ax1.imshow(self.image)
        self.dx = event.xdata
        self.dy = event.ydata

    def onrelease(self,event):
        self.fx = event.xdata
        self.fy = event.ydata
        self.ax1.plot((self.dx,self.fx),(self.dy,self.fy),'r-')
        self.tpl = (self.dx,self.fx,self.dy,self.fy)
        self.ax2.clear()
        self.ax1.figure.canvas.draw_idle()
        self.fig.canvas.mpl_disconnect(self.click)  #corrected line
        self.fig.canvas.mpl_disconnect(self.release)  # corrected line
        self._dx,self._fx,self._dy,self._fy = self.tpl[0], self.tpl[1], self.tpl[2], self.tpl[3]
        dlg = DialogScale()
        scl = dlg.ShowModal()
        if scl == wx.ID_OK:
            self.unit = dlg.comboBox1.GetValue()
            self.measure = dlg.txt.GetValue()
        print "scale", self.measure, self.unit
        self.ax2.clear()
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax1.clear()
        self.ax1.set_yticks([])
        self.ax1.set_xticks([])
        self.ax1.imshow(self.image)
        if self._fy - self._dy > self._fx - self._dx:
            self._fx = self._dx
            self.ax1.text(self._dx + 30,(float(self._fy - self._dy)/2) + self._dy, str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')
            self.nbpixels = self._fy - self._dy
        else:
            self._fy = self._dy
            self.ax1.text((float(self._fx - self._dx)/2) + self._dx, self._fy + 20,str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')
            self.nbpixels = self._fx - self._dx
        self.ax1.plot((self._dx, self._fx),(self._dy,self._fy),'r-')
        self.ax1.figure.canvas.draw_idle()
        if self.unit == 'cm':
            self._measure_ = float(self.measure) #/ 10
        elif self.unit == 'in':
            self._measure_ = float(self.measure) / 25.4
        else:
            self._measure_ = float(self.measure)


        self.pix_area = float(self._measure_) / self.nbpixels  # #lenght of a pixel side in mm
        print 'ooo', self.pix_area, self._measure_, self.nbpixels

        self.pix_area = self.pix_area * self.pix_area
        self.ax3.text(0.05,0.3,'Image scaled')
        self.scaled = (self._dx, self._fx,self._dy,self._fy) #
        #self.canvas.draw_idle() ICI
        self.ax2.clear()
        self.ax1.figure.canvas.draw_idle()
        self.StatusBar.SetStatusText("")




    def autoscalepetri(self,event):
        # automatic scaling of image that contain a petri dish
        self.StatusBar.SetStatusText("Scaling")
        print 'autoscaling'
        pimage = color.rgb2gray(io.imread('temp/temp.jpg'))
        edges = canny(pimage, sigma=2, low_threshold=0.1, high_threshold=0.3)
        hough_radii = np.arange(100, 300, 2)
        print '%', hough_radii
        hough_res = hough_circle(edges, hough_radii)
        accums, cx, cy, radii = hough_circle_peaks(hough_res, hough_radii, total_num_peaks=1)
        center_y, center_x, radius = cy[0], cx[0], radii[0]
        self.ax1.plot((center_x-radius,center_x),(center_y,center_y),'r-')
        self.ax1.plot((center_x,center_x+radius),(center_y,center_y),'r-')
        self.ax1.text(center_x, center_y + 20,'90 mm', ha = 'center',color= 'r')
        self.canvas.draw_idle()
        self.nbpixels = 2 * radius
        self.measure = 90.0
        self.pix_area = 90.0 / self.nbpixels #lenght of a pixel side in mm
        print 'ppp', self.pix_area, self.measure, self.nbpixels
        self.pix_area = self.pix_area * self.pix_area
        self.ax3.text(0.05,0.3,'Image scaled')
        self.scaled = (center_x-radius,center_x+radius,center_y,center_y)
        self.measure = 90
        self.unit = 'mm'
        self.StatusBar.SetStatusText("")


    def openEvent(self, event) :
        openDialog = wx.FileDialog(self.frame, "Open", "", "","Python files (*.jpg)|*.jpg",wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openDialog.ShowModal() == wx.ID_OK :
            filename = openDialog.GetFilename()
            self.dirname = openDialog.GetDirectory()
            self.printImageScreen(os.path.join(self.dirname, filename))
            #self.draw(os.path.join(self.dirname, self.filename))
        openDialog.Destroy()

    def printImageScreen(self,filename) :
        self.new_image_size = str(500)
        self.change_image_size()
        self.dic_cl_name = {'cl1':'Necrosis','cl2':'Leaf','cl3':'Background','cl4':'Other'}
        self.filename = filename
        self.scaled = 0
        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass
        try: self.canvas.draw_idle()
        except: pass
        self.ax1.clear()
        self.imPIL = Image.open(self.filename)
        width, height = self.imPIL.size
        self.ax3.set_xlim(0,1)
        self.ax3.set_ylim(0,1)
        self.ax3.axis('off')
        if self.scaled != 0:
            self.ax3.text(0.05,0.3,'Image scaled')
        if height > width:
            ratio = float(int(self.new_image_size))/height
            width = int(width * ratio)
            height = int(self.new_image_size)
            print width, height
        else:
            ratio = float(int(self.new_image_size))/width
            height = int(height * ratio)
            width = int(self.new_image_size)
            print width, height
        self.imPIL = self.imPIL.resize((width,height), Image.ANTIALIAS)
        self.imPIL.save('temp/temp.jpg',dpi=(300, 300))
        self.image = matplotlib.image.imread("temp/temp.jpg")   # numeracal data for rgb of the image
        self.ax1.set_xlim([0, len(self.image[0])])
        self.ax1.set_ylim([len(self.image), 0])
        self.ax1.set_aspect('equal')
        self.ax1.set_yticks([])
        self.ax1.set_xticks([])
        self.ax1.imshow(self.image)
        a, b = len(self.image), len(self.image[0])
        self.array = np.tile(np.nan, (a, b))
        print 'self.array is defined'

        self.msk = self.ax2.imshow(self.array, origin='lower',cmap = 'Greys', vmax=1, interpolation='nearest')
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.plot()
        self.ax3.text(0.05,0.7,'Image file : ' + str(os.path.split(self.filename)[-1]))
        try:            self.ax3.text(0.05,0.5,'Model selected : ' + str(self.modelname.replace('.pkl','')))
        except:            self.ax3.text(0.05,0.5,'No active model')
        if self.scaled != 0:            self.ax3.text(0.05,0.3,'Image scaled')
        self.canvas.draw_idle()
        self.data = np.array(self.image)   #variable contenant les rgb de l image
        plt.tight_layout()
        self.panel.Refresh()

    def clearEvent(self, event) :
        #clear the subplot for a white empty one
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax1.axis('off')
        self.ax2.axis('off')
        self.ax3.axis('off')
        self.ax4.axis('off')
        self.canvas.draw_idle()
        self.panel.Refresh()
        self.filename = ''
        self.dirname = ''


    def loupe_selection(self, event):
        self.empha = RectangleSelector(self.ax1, self.onselect_loupe, rectprops = dict( edgecolor = 'red', fill=False))
        connect('key_press_event', self.empha)


    def onselect_loupe(self, eclick, erelease):

        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass
        self.ax1.clear()
        self.canvas.draw_idle()


        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        nwimg = self.imPIL.crop((x1,y1,x2,y2))
        nwimg.save("temp/img2.jpg")
        self.image = matplotlib.image.imread("temp/img2.jpg")   # numeracal data for rgb of the image
        self.ax1.set_xlim([0, len(self.image[0])])
        self.ax1.set_ylim([len(self.image), 0])
        self.ax1.set_aspect('equal')
        self.ax1.imshow(self.image)
        #if self.scaled != 0:
        #    self.ax1.plot((20,20+self.nbpixels),(20,20),'r-')
        #    self.ax1.text(20+(self.nbpixels/2),30,self.measure,color = 'r',ha='center')

        a, b = len(self.image), len(self.image[0])
        self.array = np.tile(np.nan, (a, b))


        self.ax1.set_yticks([])
        self.ax1.set_xticks([])
        self.canvas.draw_idle()

        #self.data = np.array(self.image)

        self.empha.disconnect_events()
        del self.empha



    def back_to_original(self,event):

        try: self.elip.disconnect_events()
        except: pass
        try: del self.elip
        except: pass
        try: self.rect.disconnect_events()
        except: pass
        try: del self.rect
        except: pass
        try: self.lasso.disconnect_events()
        except: pass
        try: self.canvas.draw_idle()
        except: pass
        self.ax1.clear()
        self.canvas.draw_idle()



        self.image = matplotlib.image.imread("temp/temp.jpg")   # numeracal data for rgb of the image
        self.ax1.set_xlim([0, len(self.image[0])])
        self.ax1.set_ylim([len(self.image), 0])
        self.ax1.set_aspect('equal')
        self.ax1.imshow(self.image)
        a, b = len(self.image), len(self.image[0])
        self.array = np.tile(np.nan, (a, b))
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax1.set_yticks([])
        self.ax1.set_xticks([])


        self.canvas.draw_idle()



        self.panel.Refresh()





    def runFEvent(self, event):
        self.ran = 1
        self.data = np.array(self.image)
        self.data = np.rot90(self.data)
        self.data = np.flipud(self.data)
        self.selected = self.data
        self.runPrediction()

    def runSEvent(self, event):
        #self.reinit_selectclassEvent
        self.ran = 1
        self.data = np.array(self.image)
        x, y = np.meshgrid(np.arange(self.data.shape[1]), np.arange(self.data.shape[0]))
        self.pixr = np.vstack((x.flatten(), y.flatten())).T                                  #array for coordinates of pixels
        #self.lasso = LassoSelector(self.ax1, onselect=self.onselect_run)
        self.running_or_training = 1
        self.pic_tool()

    def onselect_lasso_run(self, verts):
        #prediction part - 2nd instance, capture with the lasso
        self.StatusBar.SetStatusText("Lasso selected for running")
        p = path.Path(verts)
        self.patch = patches.PathPatch(p, facecolor='None', lw=2)
        ind = self.patch.contains_points(self.pixr, radius=1)
        selected = np.zeros_like(self.data)     ################ ICI
        dd = []
        for x in self.data:
            ls = []
            for y in x:
                ls.append(str(y[0]) + '|' + str(y[1]) + '|' + str(y[2]))
            dd.append(ls)
        dd = np.array(dd)
        for x,y in zip(self.pixr, ind) :
            if y == True:
                val = dd[x[1]][x[0]]
                selected[x[1]][x[0]] = np.array([int(val.split('|')[0]),int(val.split('|')[1]),int(val.split('|')[2])])
        self.selected = cleanselection(selected)
        self.lasso.disconnect_events()
        del self.lasso
        self.runPrediction()

    def onselect_rectangle_4_run(self,eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.data = np.array(self.image)
        if self.RectangleSel == 1 and self.EllipseSel == 0 and self.LassoSel == 0:
            selected = interpret_rectangle_4_res(self.data,x1,y1,x2,y2)
        self.selected = np.flipud(selected)
        self.selected = np.rot90(self.selected)
        self.selected = np.rot90(self.selected)
        self.selected = np.rot90(self.selected)
        self.runPrediction()

    def onselect_ellipse_4_run(self,eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.data = np.array(self.image)
        if self.RectangleSel == 0 and self.EllipseSel == 1 and self.LassoSel == 0:
            selected = interpret_ellipse_4_res(self.data,x1,y1,x2,y2)
        print selected
        self.selected = np.flipud(selected)
        self.selected = np.rot90(self.selected)
        self.selected = np.rot90(self.selected)
        self.selected = np.rot90(self.selected)
        self.runPrediction()




    def runPrediction(self):
        #prediction part - 3rd instance, interpret the capture with the SVM model
        self.cl1, self.cl2, self.cl3, self.cl4 = [], [], [], []
        prob = self.svc.predict_proba([np.array([1.0,1.0,1.0])])
        self.nb_of_cl = len(prob[0])
        for x in self.selected:
            c1, c2, c3, c4 = [], [], [], []
            for y in x:
                y = np.array(y)
                if y.tolist() == [255, 255, 255]:
                    if self.nb_of_cl == 4: c4.append(np.nan)
                    if self.nb_of_cl >= 3: c3.append(np.nan)
                    if self.nb_of_cl >= 2:
                        c1.append(np.nan)
                        c2.append(np.nan)
                else:
                    tnv = []
                    tnv.append(float(y[0])/255)
                    tnv.append(float(y[1])/255)
                    tnv.append(float(y[2])/255)
                    new = np.array(tnv)
                    prob = self.svc.predict_proba([new])
                    if len(prob[0]) == 2:
                        if prob[0][0] >= prob[0][1]:
                            c1.append(prob[0][0])
                            c2.append(np.nan)
                        else:
                            c1.append(np.nan)
                            c2.append(0.5)
                    elif len(prob[0]) == 3:
                        if prob[0][0] >= prob[0][1] and prob[0][0] >= prob[0][2]:
                            c1.append(prob[0][0])
                            c2.append(np.nan)
                            c3.append(np.nan)
                        elif prob[0][1] >= prob[0][0] and prob[0][1] >= prob[0][2]:
                            c1.append(np.nan)
                            c2.append(0.5)
                            c3.append(np.nan)
                        else:
                            c1.append(np.nan)
                            c2.append(np.nan)
                            c3.append(prob[0][1])
                    else:
                        if prob[0][0] >= prob[0][1] and prob[0][0] >= prob[0][2] and prob[0][0] >= prob[0][3]:
                            c1.append(prob[0][0])
                            c2.append(np.nan)
                            c3.append(np.nan)
                            c4.append(np.nan)
                        elif prob[0][1] > prob[0][0] and prob[0][1] >= prob[0][2] and prob[0][1] >= prob[0][3]:
                            c1.append(np.nan)
                            c2.append(0.5)
                            c3.append(np.nan)
                            c4.append(np.nan)
                        elif prob[0][2] > prob[0][0] and prob[0][2] > prob[0][1] and prob[0][2] >= prob[0][3]:
                            c1.append(np.nan)
                            c2.append(np.nan)
                            c3.append(prob[0][1])
                            c4.append(np.nan)
                        else:
                            c1.append(np.nan)
                            c2.append(np.nan)
                            c3.append(np.nan)
                            c4.append(prob[0][3])
            self.cl1.append(c1)
            self.cl2.append(c2)
            self.cl3.append(c3)
            self.cl4.append(c4)
        self.ax2.clear()

        self.cl1 = np.rot90(self.cl1)
        self.cl2 = np.rot90(self.cl2)
        self.cl3 = np.rot90(self.cl3)
        self.cl4 = np.rot90(self.cl4)
        self.cl1 = np.flipud(self.cl1)
        self.cl2 = np.flipud(self.cl2)
        self.cl3 = np.flipud(self.cl3)
        self.cl4 = np.flipud(self.cl4)
        n, m , p , q = 0, 0, 0, 0
        n, m, p, q  = countpix(self.cl1), countpix(self.cl2), countpix(self.cl3), countpix(self.cl4)
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.set_xlim([0,len(self.cl1[0])])
        self.ax2.set_ylim([len(self.cl1),0])
        self.ax2.imshow(self.cl1,vmin = 0, vmax= 1, origin='lower')
        self.ax2.imshow(self.cl2,cmap='Greys',vmin = 0, vmax = 1, origin='lower')
        self.nbpix = (n,m,p,q)
        self.ratio_12 = round(float(n)/(m + n),3)
        if self.scaled != 0:
            if self.scaled[3] - self.scaled[2] > self.scaled[1] - self.scaled[0]:
                self.ax1.text(self.scaled[0] + 30,(float(self.scaled[3] - self.scaled[2])/2) + self.scaled[2], str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')
            else:
                self.ax1.text((float(self.scaled[1] - self.scaled[0])/2) + self.scaled[0], self.scaled[3] + 20,str(self.measure) + ' ' + str(self.unit),ha = 'center', va = 'center',color = 'r')
            self.ax1.plot((self.scaled[0],self.scaled[1]),(self.scaled[2],self.scaled[3]),'r-')       #self.scaled = (self._dx, self._fx,self._dy,self._fy)
        self.canvas.draw_idle()
        self.panel_four()

    def panel_four(self):
        self.ax4.clear()
        self.ax4.axis('off')
        self.ax4.set_ylim(0,1)
        self.ax4.set_xlim(0,1)
        self.ax4.text(0.25,0.95,self.dic_cl_name['cl1'] + ' : ' + str(self.nbpix[0]) + ' pixels')
        self.ax4.text(0.25,0.85,self.dic_cl_name['cl2'] + ' : ' + str(self.nbpix[1]) + ' pixels')
        self.ax4.text(0.25,0.75,self.dic_cl_name['cl3'] + ' : ' + str(self.nbpix[2]) + ' pixels')
        self.ax4.text(0.25,0.65,self.dic_cl_name['cl4'] + ' : ' + str(self.nbpix[3]) + ' pixels')
        self.ax4.text(0.25,0.55,'Ratio ' + self.dic_cl_name['cl1'] + '/(' + self.dic_cl_name['cl1'] + '+' + self.dic_cl_name['cl2'] + ') = ' + str(self.ratio_12))
        if self.scaled != 0:
            self.ax4.text(0.25,0.40, self.dic_cl_name['cl1'] +  ' area : ' + str(round(self.nbpix[0] * self.pix_area,3))+ ' ' + self.unit + '2')
            self.ax4.text(0.25,0.30, self.dic_cl_name['cl2'] +  ' area : ' + str(round(self.nbpix[1] * self.pix_area,3))+ ' ' + self.unit + '2')
            self.ax4.text(0.25,0.20, self.dic_cl_name['cl3'] +  ' area : ' + str(round(self.nbpix[2] * self.pix_area,3))+ ' ' + self.unit + '2')
            self.ax4.text(0.25,0.10, self.dic_cl_name['cl4'] +  ' area : ' + str(round(self.nbpix[3] * self.pix_area,3))+ ' ' + self.unit + '2')
        self.canvas.draw_idle()

    def saveit(self,event):
        now = datetime.now()
        current_time = now.strftime("%H_%M_%S")
        today = date.today()
        current_date = today.strftime("%d_%m_%Y")
        self.new_name = os.path.split(self.filename)[-1]
        init_name = self.new_name
        self.rename_image()
        print 'LE NOUVEAU NOM', self.new_name
        plt.savefig(os.path.join('my_images_out', self.new_name + '_' + current_time + '_' + current_date + '.png'))
        print 'SAVING DONE'
        self.ax3.clear()
        self.ax3.set_xlim(0, 1)
        self.ax3.set_ylim(0, 1)
        self.ax3.axis('off')
        self.ax3.text(0.05,0.7,'Image file : ' + str(os.path.split(self.filename)[-1]))
        try:
            self.ax3.text(0.05,0.5,'Model selected : ' + str(self.modelname.replace('.pkl','')))
        except:
            self.ax3.text(0.05,0.5,'No active model')
        if self.scaled != 0:
            self.ax3.text(0.05,0.3,'Image scaled')
        self.ax3.text(0.05, 0.1, self.new_name + '_' + current_time + '_' + current_date + '.png saved')
        self.canvas.draw_idle()
        log = open(self.datapoint + '.xls','a')
        if self.op == 0:
            log.write('Original image name\tNew name\tTime\tDate\tNb. pixels necrosis\tNb. pixels leaf\tNb. pixels background\tNb. Pixel other\tRatio pixels necrosis/leaf\tNecrosis area\tLeaf area\tunit\n')
            self.op = 1
        outowrite = init_name + '\t' + self.new_name + '\t' + current_time + '\t' + current_date +  '\t'
        outowrite = outowrite + str(self.nbpix[0]) + '\t'+ str(self.nbpix[1]) + '\t' + str(self.nbpix[2]) + '\t' + str(self.nbpix[3]) + '\t'
        outowrite = outowrite + str(self.ratio_12) + '\t'
        if self.scaled != 0:
                outowrite = outowrite + str(round(self.nbpix[0] * self.pix_area,3)) + '\t' + str(round(self.nbpix[1] * self.pix_area,3)) + '\t' + str(self.unit) + "2"
        log.write(outowrite + '\n')
        log.close()

    def erase_selection(self,event):
        xc, yc = np.meshgrid(np.arange(len(self.cl1[0])), np.arange(len(self.cl1)))
        self.pix_cor = np.vstack((xc.flatten(), yc.flatten())).T  #array for coordinates of pixels
        self.lasso_cor = LassoSelector(self.ax2, onselect=self.onselect_erra)

    def onselect_erra(self, verts):
        p = path.Path(verts)
        ind = p.contains_points(self.pix_cor, radius=1)  #contains the false and true
        if self.nb_of_cl == 4:
            self.cl4 = updateArray(self.cl4, ind, 4)
        if self.nb_of_cl >= 3:
            self.cl3 = updateArray(self.cl3, ind, 4)
        if self.nb_of_cl >= 2:
            self.cl2 = updateArray(self.cl2, ind, 4)
            self.cl1 = updateArray(self.cl1, ind, 4)
        self.lasso_cor.disconnect_events()
        del self.lasso_cor
        self.ax2.clear()
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.set_xlim([0,len(self.cl1[0])])
        self.ax2.set_ylim([len(self.cl1),0])
        self.ax2.imshow(self.cl1,vmin = 0, vmax= 1, origin='lower')
        self.ax2.imshow(self.cl2,cmap='Greys',vmin = 0, vmax = 1, origin='lower')
        n = countpix(self.cl1)
        m = countpix(self.cl2)
        p = countpix(self.cl3)
        q = countpix(self.cl4)
        self.nbpix = (n,m,p,q)
        self.ratio_12 = round(float(n)/(m + n),3)
        self.canvas.draw_idle()
        self.panel_four()

    def fill_selection(self,event):
        dlg = DialogModify(self.dic_cl_name,'Fill with pixels')
        res_fill = dlg.ShowModal()
        if res_fill == wx.ID_OK:
                self.fill = (dlg.rd1.GetValue(), dlg.rd2.GetValue(), dlg.rd3.GetValue(), dlg.rd4.GetValue())

        xc, yc = np.meshgrid(np.arange(len(self.cl1[0])), np.arange(len(self.cl1)))
        self.pix_fill = np.vstack((xc.flatten(), yc.flatten())).T  #array for coordinates of pixels
        self.lasso_fill = LassoSelector(self.ax2, onselect=self.onselect_fill)



    def onselect_fill(self, verts):
        p = path.Path(verts)
        ind = p.contains_points(self.pix_fill, radius=1)  #contains the false and true

        if self.fill[0] == True:
            self.cl1 = updateArray(self.cl1, ind, 6)
            self.cl2 = updateArray(self.cl2, ind, 4)
            try:
                self.cl3 = updateArray(self.cl3, ind, 4)
            except:
                pass
            try:
                self.cl4 = updateArray(self.cl4, ind, 4)
            except:
                pass

        elif self.fill[1] == True:
            self.cl2 = updateArray(self.cl2, ind, 5)
            self.cl1 = updateArray(self.cl1, ind, 4)
            try:
                self.cl3 = updateArray(self.cl3, ind, 4)
            except:
                pass
            try:
                self.cl4 = updateArray(self.cl4, ind, 4)
            except:
                pass


        elif self.fill[2] == True:
            self.cl3 = updateArray(self.cl3, ind, 4)
            self.cl1 = updateArray(self.cl1, ind, 4)
            self.cl2 = updateArray(self.cl2, ind, 4)
            try:
                self.cl4 = updateArray(self.cl4, ind, 4)
            except:
                pass


        elif self.fill[3] == True:
            self.cl4 = updateArray(self.cl4, ind, 4)
            self.cl2 = updateArray(self.cl2, ind, 4)
            self.cl3 = updateArray(self.cl3, ind, 4)
            self.cl1 = updateArray(self.cl1, ind, 4)

        self.lasso_fill.disconnect_events()
        del self.lasso_fill


        self.ax2.clear()
        self.ax2.set_yticks([])
        self.ax2.set_xticks([])
        self.ax2.set_xlim([0,len(self.cl1[0])])
        self.ax2.set_ylim([len(self.cl1),0])
        self.ax2.imshow(self.cl1,vmin = 0, vmax= 1, origin='lower')
        self.ax2.imshow(self.cl2,cmap='Greys',vmin = 0, vmax = 1, origin='lower')

        n = countpix(self.cl1)
        m = countpix(self.cl2)
        p = countpix(self.cl3)
        q = countpix(self.cl4)


        self.nbpix = (n,m,p,q)
        self.ratio_12 = round(float(n)/(m + n),3)
        self.canvas.draw_idle()
        self.panel_four()



    def rename_image(self):
        dlg = DialogRename('Rename image',self.new_name)
        res_fill = dlg.ShowModal()
        if res_fill == wx.ID_OK:
                self.new_name = (dlg.txtrn.GetValue())



    def change_image_size(self):
        dlg = DialogReSize('Change image size',self.new_image_size)

        res_chsize = dlg.ShowModal()
        if res_chsize == wx.ID_OK:
                self.new_image_size = (dlg.txtrns.GetValue())


class DialogReSize(wx.Dialog):
    """"""
    def __init__(self,phrase,thesize):
        """Constructor"""
        wx.Dialog.__init__(self, None, title=phrase,size=(250, 200))
        txt1 = wx.StaticText(self, label="Image size can be modified")
        txt2 = wx.StaticText(self, label="    Enter a size between 500 and 1500 pixels (default = 500)")
        self.txtrns = wx.TextCtrl(self, value=thesize)
        okBtn = wx.Button(self, wx.ID_OK)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(txt1, 0, wx.ALL | wx.CENTER, 5)
        vbox.Add(txt2, 0, wx.ALL|wx.CENTER, 5)

        hbox.Add(self.txtrns, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vbox)





class DialogRename(wx.Dialog):
    """"""
    def __init__(self,phrase,thename):
        """Constructor"""
        print'Voici the name', thename
        wx.Dialog.__init__(self, None, title=phrase,size=(250, 100))
        self.txtrn = wx.TextCtrl(self, value=thename)
        okBtn = wx.Button(self, wx.ID_OK)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.txtrn, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vbox)



class DialogModify(wx.Dialog):
    """"""
    def __init__(self,dicl,phrase):

        wx.Dialog.__init__(self, None, title=phrase,size=(250, 270))
        txt = wx.StaticText(self, label="Select a class : ")
        txt1 = wx.StaticText(self, label=dicl["cl1"] )
        txt2 = wx.StaticText(self, label=dicl["cl2"] )
        txt3 = wx.StaticText(self, label=dicl["cl3"] )
        txt4 = wx.StaticText(self, label=dicl["cl4"] )

        self.rd1 = wx.RadioButton(self)
        self.rd2 = wx.RadioButton(self)
        self.rd3 = wx.RadioButton(self)
        self.rd4 = wx.RadioButton(self)

        okBtn = wx.Button(self, wx.ID_OK)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(txt1, 0, wx.ALL|wx.CENTER, 5)
        hbox1.Add(self.rd1, 0, wx.ALL|wx.CENTER, 5)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(txt2, 0, wx.ALL|wx.CENTER, 5)
        hbox2.Add(self.rd2, 0, wx.ALL|wx.CENTER, 5)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(txt3, 0, wx.ALL|wx.CENTER, 5)
        hbox3.Add(self.rd3, 0, wx.ALL|wx.CENTER, 5)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(txt4, 0, wx.ALL|wx.CENTER, 5)
        hbox4.Add(self.rd4, 0, wx.ALL|wx.CENTER, 5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(txt, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox1, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox2, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox3, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox4, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vbox)



class DialogClasses(wx.Dialog):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, dicl):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Build training classes",size=(200, 250))
        self.rd1 = wx.RadioButton(self)
        self.rd2 = wx.RadioButton(self)
        self.rd3 = wx.RadioButton(self)
        self.rd4 = wx.RadioButton(self)
        self.txt1 = wx.TextCtrl(self, value=dicl["cl1"])
        self.txt2 = wx.TextCtrl(self, value=dicl["cl2"])
        self.txt3 = wx.TextCtrl(self, value=dicl["cl3"])
        self.txt4 = wx.TextCtrl(self, value=dicl["cl4"])
        okBtn = wx.Button(self, wx.ID_OK)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.txt1, 0, wx.ALL|wx.CENTER, 3)
        hbox1.Add(self.rd1, 0, wx.ALL|wx.CENTER, 3)
        vbox.Add(hbox1, 0, wx.ALL|wx.CENTER, 10)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.txt2, 0, wx.ALL|wx.CENTER, 3)
        hbox2.Add(self.rd2, 0, wx.ALL|wx.CENTER, 3)
        vbox.Add(hbox2, 0, wx.ALL|wx.CENTER, 5)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(self.txt3, 0, wx.ALL|wx.CENTER, 3)
        hbox3.Add(self.rd3, 0, wx.ALL|wx.CENTER, 3)
        vbox.Add(hbox3, 0, wx.ALL|wx.CENTER, 5)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(self.txt4, 0, wx.ALL|wx.CENTER,3)
        hbox4.Add(self.rd4, 0, wx.ALL|wx.CENTER, 3)
        vbox.Add(hbox4, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(okBtn, 0, wx.ALL|wx.CENTER, 10)
        self.SetSizer(vbox)




def wx_ask_question_windowed(question, caption):
    app = wx.App()
    dlg = wx.MessageDialog(None, question, caption, wx.YES_NO | wx.ICON_INFORMATION)
    dlg.Center()
    dlg_result = dlg.ShowModal()
    result = dlg_result == wx.ID_YES
    dlg.Destroy()
    app.MainLoop()
    app.Destroy()
    return result

class PickMore(wx.Dialog):
    def __init__(self,nom):
        wx.Dialog.__init__(self,None, title="",size=(250, 100))
        st = wx.StaticText(self, label='Do you want to select more ' + nom + ' ?', style=wx.ALIGN_LEFT)
        yes = wx.Button(self, wx.ID_OK)
        no = wx.Button(self, wx.ID_CANCEL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox.Add(yes, 0, wx.ALL | wx.CENTER, 5)
        hbox.Add(no, 0, wx.ALL | wx.CENTER, 5)
        vbox.Add(st, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vbox)





class DialogScale(wx.Dialog):
    """"""
    def __init__(self):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Add a scale",size=(250, 100))
        self.txt = wx.TextCtrl(self, value="Enter a value")
        self.comboBox1 = wx.ComboBox(self,choices=['cm'],value="mm")
        okBtn = wx.Button(self, wx.ID_OK)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.txt, 0, wx.ALL|wx.CENTER, 5)
        hbox.Add(self.comboBox1, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(hbox, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vbox)




class DialogTrain(wx.Dialog):
    """"""
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Model training",size=(360, 170))
        st1 = wx.StaticText(self, label='Select and existing model', style=wx.ALIGN_LEFT)
        self.comboBox1 = wx.ComboBox(self,choices=glob.glob('*.pkl'),value="")
        st2 = wx.StaticText(self, label='Build a new model from selected classes', style=wx.ALIGN_LEFT)
        self.txt = wx.TextCtrl(self, value="Model name")
        okBtn = wx.Button(self, wx.ID_OK)
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(st1, 0, wx.ALL|wx.CENTER, 5)
        hsizer1.Add(self.comboBox1, 0, wx.ALL|wx.CENTER, 5)
        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(st2, 0, wx.ALL|wx.CENTER, 5)
        hsizer2.Add(self.txt, 0, wx.ALL|wx.CENTER, 5)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(hsizer1, 0, wx.ALL|wx.CENTER, 5)
        vsizer.Add(hsizer2, 0, wx.ALL|wx.CENTER, 5)
        vsizer.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vsizer)


class DialogPlease(wx.Dialog):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, val, _size_):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Model training",size=_size_)
        if val == 1:            st1 = wx.StaticText(self, label='Please select 2 to 4 classes\nbefore creating a new model', style=wx.ALIGN_CENTER)
        elif val == 2:            st1 = wx.StaticText(self, label='Please select and existing\nmodel or create a new one\nby selecting 2 to 4 classes', style=wx.ALIGN_CENTER)
        elif val == 3:            st1 = wx.StaticText(self, label='Please, click on the line to add a value and unit', style=wx.ALIGN_CENTER)
        okBtn = wx.Button(self, wx.ID_OK)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(st1, 0, wx.ALL|wx.CENTER, 20)
        vsizer.Add(okBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(vsizer)
        self.Centre()







class Learning():
    def __init__(self):
        self.X, self.y = [], []
        self.readfichier('class1_tp',0,2000)
        self.readfichier('class2_tp',1,2000)
        self.readfichier('class3_tp',2,2000)
        self.readfichier('class4_tp',3,2000)
        self.y = np.array(self.y)
        self.X = np.array(self.X)

    def readfichier(self,fichier,v,nbre):
        if os.path.isfile(fichier) == True:
            fx = open(fichier)
            cont = fx.readlines()
            fx.close()
            i = 0
            #lst = []
            while i < nbre:
                print i, nbre
                nb = random.choice(cont)
                #if nb not in lst:
                #lst.append(nb)
                nls = []
                nls.append(float(nb.split(',')[0].replace('(',''))/255)
                nls.append(float(nb.split(',')[1])/255)
                nls.append(float(nb.split(',')[2].replace(')',''))/255)
                self.X.append(np.array(nls))
                self.y.append(v)
                i = i + 1

    def runSVC(self,modelname):
        svc = svm.SVC(kernel='linear', C=1.0, probability=True).fit(self.X, self.y)  #
        ####### saving the model ##############
        if os.path.isfile(modelname) == False:
            fx = open(modelname,'w')
            fx.close()
        joblib.dump(svc, modelname)
        return svc


if __name__ == '__main__':
    app = MyGUIApp()
    app.MainLoop()




