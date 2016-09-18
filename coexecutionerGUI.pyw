import wx
import wx.lib.scrolledpanel
import mysocket
import select

class MyFrame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self):
        self.requests={}
        wx.Frame.__init__(self,None,-1,"Coexecutioner",size=(650,400))
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, style=wx.SIMPLE_BORDER)
        self.panel.SetupScrolling()
        self.panel.SetBackgroundColour('#FFFFFF')
        self.rows = wx.BoxSizer(wx.VERTICAL)
        self.nameField = wx.TextCtrl(self.panel, style=wx.TE_LEFT)
        self.connect = wx.Button(self.panel,label="Connect")
        self.instruction1 = wx.StaticText(self.panel, label="Enter coexecutioner name:")
        self.hostField = wx.TextCtrl(self.panel,style=wx.TE_LEFT)
        self.instruction2 = wx.StaticText(self.panel, label="Enter host name:")
        self.portField = wx.TextCtrl(self.panel,style=wx.TE_LEFT)
        self.instruction3 = wx.StaticText(self.panel, label="Enter port number:")
        self.AddRow(self.instruction1)
        self.AddRow(self.nameField)
        self.AddRow(self.instruction2)
        self.AddRow(self.hostField)
        self.AddRow(self.instruction3)
        self.AddRow(self.portField)
        self.AddRow(self.connect)

        self.timer = wx.Timer(self.panel)
        self.panel.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.panel.Bind(wx.EVT_BUTTON, self.Connect, self.connect)

        self.SetIcon(wx.Icon('images/databaseIcon.ico', wx.BITMAP_TYPE_ICO))
        
    def Connect(self, evt):
        name = self.nameField.GetValue()
        if name:
            try:
                if not self.hostField.GetValue():
                    host = 'localhost'
                else:
                    host = self.hostField.GetValue()
                if not self.portField.GetValue().isdigit():
                    port = 2223
                else:
                    port = int(self.portField.GetValue())
                self.s = mysocket.MySocket()
                self.s.connect(host,port)
                self.s.send("coexecutioner")
                self.s.send(name)
                self.RemoveRow(self.nameField)
                self.RemoveRow(self.connect)
                self.RemoveRow(self.instruction1)
                self.RemoveRow(self.instruction2)
                self.RemoveRow(self.instruction3)
                self.RemoveRow(self.hostField)
                self.RemoveRow(self.portField)
                self.AddRow(wx.StaticText(self.panel, label="Hello "+name+", coexecution requests will appear below:"))
                
                self.timer.Start(100)
            except:
                self.instruction1.SetLabel("Could not connect to host and port. Enter coexecutioner name:")
                self.panel.Layout()
                print sys.exc_info()
    def update(self, evt):
        socket_list=[self.s.sock]
        ready_to_read,ready_to_write,in_error = select.select(socket_list, [], [], 0)
        for sock in ready_to_read:
            data=self.s.receive().split('|')
            if data[0] == 'Add':
                self.AddRequest(data[1],data[2],data[3],data[4])
            elif data[0] == 'Remove':
                self.RemoveRequest(data[1],data[2])
        
    def AddRequest(self,usernameText,queryNum,queryText,tablesText):
        font = wx.Font(14,wx.FONTFAMILY_ROMAN,wx.FONTSTYLE_ITALIC,wx.FONTWEIGHT_BOLD)
        row = wx.BoxSizer(wx.HORIZONTAL)
        
        username = wx.StaticText(self.panel, label=usernameText)
        query = wx.StaticText(self.panel, label=queryText)
        tables = wx.StaticText(self.panel, label=tablesText)
        username.Wrap(100)
        query.Wrap(185)
        tables.Wrap(100)
        approve = wx.BitmapButton(self.panel,bitmap=wx.Bitmap('images/accept.jpg',wx.BITMAP_TYPE_JPEG))
        deny = wx.BitmapButton(self.panel,bitmap=wx.Bitmap('images/deny.jpg',wx.BITMAP_TYPE_JPEG))
        
        column1 = wx.BoxSizer(wx.VERTICAL)
        userHeading = wx.StaticText(self.panel,label="Executor:")
        userHeading.SetFont(font)
        column1.Add(userHeading,0,wx.ALIGN_CENTER)
        column1.Add(username,0,wx.ALIGN_CENTER)
        row.Add(column1,0,wx.ALL,10)
        
        column2 = wx.BoxSizer(wx.VERTICAL)
        queryHeading = wx.StaticText(self.panel,label="wants to execute query:")
        queryHeading.SetFont(font)
        column2.Add(queryHeading,0,wx.ALIGN_CENTER)
        column2.Add(query,0,wx.ALIGN_CENTER)
        row.Add(column2,0,wx.ALL,10)

        column3 = wx.BoxSizer(wx.VERTICAL)
        tablesHeading = wx.StaticText(self.panel,label="Sensitive fields:")
        tablesHeading.SetFont(font)
        column3.Add(tablesHeading,0,wx.ALIGN_CENTER)
        column3.Add(tables,0,wx.ALIGN_CENTER)
        row.Add(column3,0,wx.ALL,10)
        
        row.Add(approve,0,wx.ALL,10)
        row.Add(deny,0,wx.ALL,10)
        
        approve.Bind(wx.EVT_BUTTON, lambda evt, temp=usernameText, temp2=queryNum: self.OnApprove(evt, temp, temp2))
        deny.Bind(wx.EVT_BUTTON, lambda evt, temp=usernameText, temp2=queryNum: self.OnDeny(evt, temp, temp2))
        
        self.requests[usernameText+'|'+queryNum] = row
        self.AddRow(row)
        
    def OnDeny(self,e,username,num):
        self.RemoveRequest(username,num)
        self.s.send("Deny|"+username+"|"+num)

    def OnApprove(self,e,username,num):
        self.RemoveRequest(username,num)
        self.s.send("Approve|"+username+"|"+num)

    def RemoveRequest(self,name,queryNum):
        if name+'|'+queryNum in self.requests:
            self.RemoveRow(self.requests[name+'|'+queryNum])
            del self.requests[name+'|'+queryNum]

    def RemoveRow(self,row):
        self.rows.Hide(row)
        self.rows.Remove(row)
        self.panel.SetSizer(self.rows)
        self.Layout()
        self.panel.Layout()
        self.panel.FitInside()

    def AddRow(self,row):
        self.rows.Add(row,0,wx.ALIGN_CENTER)
        self.panel.SetSizer(self.rows)
        self.Layout()
        self.panel.Layout()
        self.panel.FitInside()
        
#app = wx.App(False)
#To get errors use the following instead...
app = wx.App(True,'Error_Coexecutioner.txt')
frame = MyFrame()
frame.Show(True)

app.MainLoop()
