import wx
import wx.lib.scrolledpanel
import mysocket
import select
import sys

class MyFrame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self):
        self.requests={}
        wx.Frame.__init__(self,None,-1,"Executor",size=(645,450))
        self.topPanel = wx.Panel(self)
        self.statusText = wx.StaticText(self,label="Results will display below...")
        self.statusText.Wrap(640)
        self.bottomPanel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, style=wx.SIMPLE_BORDER)
        self.bottomPanel.SetupScrolling()
        self.bottomPanel.SetAutoLayout(1)
        self.bottomPanel.SetBackgroundColour('#DDDDDD')
        self.resultsText = wx.StaticText(self.bottomPanel)
        self.resultsText.Wrap(640)
        self.resultsTextSizer = wx.BoxSizer(wx.VERTICAL)
        self.resultsTextSizer.Add(self.resultsText)
        self.bottomPanel.SetSizer(self.resultsTextSizer)
        self.topPanel.SetBackgroundColour('#FFFFFF')
        self.panels = wx.BoxSizer(wx.VERTICAL)
        self.panels.Add(self.topPanel,2,wx.ALIGN_CENTER|wx.EXPAND)
        self.panels.Add(self.statusText,0,wx.ALIGN_LEFT)
        self.panels.Add(self.bottomPanel,5,wx.ALIGN_CENTER|wx.EXPAND)
        self.rows = wx.BoxSizer(wx.VERTICAL)
        self.nameField = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
        self.connect = wx.Button(self.topPanel,label="Connect")
        self.instruction1 = wx.StaticText(self.topPanel, label="Enter executor name:")
        self.hostField = wx.TextCtrl(self.topPanel,style=wx.TE_LEFT)
        self.instruction2 = wx.StaticText(self.topPanel, label="Enter host name:")
        self.portField = wx.TextCtrl(self.topPanel,style=wx.TE_LEFT)
        self.instruction3 = wx.StaticText(self.topPanel, label="Enter port number:")
        self.rows.Add(self.instruction1,0,wx.ALIGN_CENTER)
        self.rows.Add(self.nameField,0,wx.ALIGN_CENTER)
        self.rows.Add(self.instruction2,0,wx.ALIGN_CENTER)
        self.rows.Add(self.hostField,0,wx.ALIGN_CENTER)
        self.rows.Add(self.instruction3,0,wx.ALIGN_CENTER)
        self.rows.Add(self.portField,0,wx.ALIGN_CENTER)
        self.rows.Add(self.connect,0,wx.ALIGN_CENTER)
        self.topPanel.SetSizer(self.rows)
        self.SetSizer(self.panels)

        self.statuses = ({0:"Click execute to display all patient information",
                     1:"Click execute to display all patient names",
                     2:"Enter a patient's first and last name and click execute to display patient info",
                     3:"Click execute to display patient and location information joined by address",
                     4:"Click execute to display all location information",
                     5:"Enter a location name and click execute to delete that location",
                     6:"Enter new location information and click execute to add that location",
                     7:"Enter a location name and the name you'd like to change it to and click execute"})
        self.results = {0:"",1:"",2:"",3:"",4:"",5:"",6:"",7:""}
        self.queries = {0:"",1:"",2:"",3:"",4:"",5:"",6:"",7:""}
        self.selected = -1
        
        self.timer = wx.Timer(self.topPanel)
        self.topPanel.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.topPanel.Bind(wx.EVT_BUTTON, self.Connect, self.connect)

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
                self.s.send("executor")
                self.s.send(name)
                self.rows.Hide(self.nameField)
                self.rows.Hide(self.connect)
                self.rows.Hide(self.instruction2)
                self.rows.Hide(self.hostField)
                self.rows.Hide(self.instruction3)
                self.rows.Hide(self.portField)
                self.rows.Remove(self.nameField)
                self.rows.Remove(self.connect)
                self.rows.Remove(self.instruction2)
                self.rows.Remove(self.hostField)
                self.rows.Remove(self.instruction3)
                self.rows.Remove(self.portField)
                self.instruction1.SetLabel("Hello "+name+", click a query button and execute to see results:")
                self.queryButtons1 = wx.BoxSizer(wx.HORIZONTAL)
                self.queryButtons2 = wx.BoxSizer(wx.HORIZONTAL)
                self.executeRow = wx.BoxSizer(wx.HORIZONTAL)
                
                self.button1 = wx.Button(self.topPanel, label="All Patients")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query1, self.button1)
                self.button2 = wx.Button(self.topPanel, label="Patient Names")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query2, self.button2)
                self.button3 = wx.Button(self.topPanel, label="Patient by Name")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query3, self.button3)
                self.button4 = wx.Button(self.topPanel, label="Patients with Location")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query4, self.button4)
                self.button5 = wx.Button(self.topPanel, label="All Locations")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query5, self.button5)
                self.button6 = wx.Button(self.topPanel, label="Location Delete")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query6, self.button6)
                self.button7 = wx.Button(self.topPanel, label="Location Insert")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query7, self.button7)
                self.button8 = wx.Button(self.topPanel, label="Location Update")
                self.topPanel.Bind(wx.EVT_BUTTON, self.Query8, self.button8)
                
                self.queryButtons1.Add(self.button1)
                self.queryButtons1.Add(self.button2)
                self.queryButtons1.Add(self.button3)
                self.queryButtons1.Add(self.button4)
                self.queryButtons1.Add(self.button5)
                self.queryButtons2.Add(self.button6)
                self.queryButtons2.Add(self.button7)
                self.queryButtons2.Add(self.button8)
                
                self.rows.Add(self.queryButtons1,0,wx.ALIGN_CENTER)
                self.rows.Add(self.queryButtons2,0,wx.ALIGN_CENTER)
                self.rows.Add(self.executeRow,1)
                self.Layout()
                
                self.timer.Start(100)
            except:
                self.instruction1.SetLabel("Could not connect to host and port. Enter executor name:")
                self.Layout()
                print sys.exc_info()

    def update(self, evt):
        socket_list=[self.s.sock]
        ready_to_read,ready_to_write,in_error = select.select(socket_list, [], [], 0)
        for sock in ready_to_read:
            data = self.s.receive().split('|!|')
            number = data[0]
            results = data[1]
            number = int(number)
            self.results[number] = results
            self.statuses[number] = 'Displaying results for query... '+self.queries[number]
            if number==self.selected:
                if results.startswith('Waiting'):
                    self.statusText.SetLabel(results)
                else:
                    if results.startswith('ERROR'):
                        self.getButton(number).SetBackgroundColour('#C50202')#dark red for error
                    else:
                        self.getButton(number).SetBackgroundColour('#229702')#dark green for success
                    self.statusText.SetLabel('Displaying results for query... '+self.queries[number])
                    self.resultsText.SetLabel(results)
                    self.executeRow.ShowItems(True)
                    self.bottomPanel.FitInside()
            else:
                if results.startswith('ERROR'):
                    self.getButton(number).SetBackgroundColour('#FF141E')
                else:
                    self.getButton(number).SetBackgroundColour('#31F000')
            self.Layout()
                
        
        
    def Query1(self, evt):
        if self.selected != 0:
            self.selected = 0
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[0])
            self.resultsText.SetLabel(self.results[0])
            if self.statuses[0].startswith('Waiting'):
                self.button1.SetBackgroundColour('#BD8000')
            else:
                if self.results[0].startswith('ERROR') or self.statuses[0].startswith('ERROR'):
                    self.button1.SetBackgroundColour('#C50202')
                    self.execute1 = wx.Button(self.topPanel, label="Re-Execute")
                elif self.statuses[0].startswith('Displaying'):
                    self.button1.SetBackgroundColour('#229702')
                    self.execute1 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button1.SetBackgroundColour('#ABABAB')
                    self.execute1 = wx.Button(self.topPanel, label="Execute")
                self.executeRow.Add(self.execute1,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute1, self.execute1)
            self.Layout()
    def Execute1(self, evt):
        self.statuses[0] = 'Waiting for result from server...'
        self.statusText.SetLabel('Waiting for result from server...')
        self.queries[0]='SELECT * FROM PATIENT'
        self.button1.SetBackgroundColour('#BD8000')
        self.executeRow.ShowItems(False)
        self.s.send('0|SELECT * FROM PATIENT')


    def Query2(self, evt):
        if self.selected != 1:
            self.selected = 1
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[1])
            self.resultsText.SetLabel(self.results[1])
            if self.statuses[1].startswith('Waiting'):
                self.button2.SetBackgroundColour('#BD8000')
            else:
                if self.results[1].startswith('ERROR') or self.statuses[1].startswith('ERROR'):
                    self.button2.SetBackgroundColour('#C50202')
                    self.execute2 = wx.Button(self.topPanel, label="Re-Execute")
                    
                elif self.statuses[1].startswith('Displaying'):
                    self.button2.SetBackgroundColour('#229702')
                    self.execute2 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button2.SetBackgroundColour('#ABABAB')
                    self.execute2 = wx.Button(self.topPanel, label="Execute")
                self.executeRow.Add(self.execute2,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute2, self.execute2)
            self.Layout()
    def Execute2(self, evt):
        self.statuses[1] = 'Waiting for result from server...'
        self.statusText.SetLabel('Waiting for result from server...')
        self.queries[1]='SELECT FNAME, LNAME FROM PATIENT'
        self.button2.SetBackgroundColour('#BD8000')
        self.executeRow.ShowItems(False)
        self.s.send('1|SELECT FNAME, LNAME FROM PATIENT')

    def Query3(self, evt):
        if self.selected != 2:
            self.selected = 2
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[2])
            self.resultsText.SetLabel(self.results[2])
            if self.statuses[2].startswith('Waiting'):
                self.button3.SetBackgroundColour('#BD8000')
            else:
                if self.results[2].startswith('ERROR') or self.statuses[2].startswith('ERROR'):
                    self.button3.SetBackgroundColour('#C50202')
                    self.execute3 = wx.Button(self.topPanel, label="Re-Execute")
                elif self.statuses[2].startswith('Displaying'):
                    self.button3.SetBackgroundColour('#229702')
                    self.execute3 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button3.SetBackgroundColour('#ABABAB')
                    self.execute3 = wx.Button(self.topPanel, label="Execute")
                self.textCtrl1 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.textCtrl2 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.fname = wx.StaticText(self.topPanel, label="Patient first name:")
                self.lname = wx.StaticText(self.topPanel, label="Patient last name:")
                self.executeRow.Add(self.fname,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl1,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.lname,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl2,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.execute3,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute3, self.execute3)
            self.Layout()
    def Execute3(self, evt):
        if self.textCtrl1.GetValue().strip() == '' or self.textCtrl2.GetValue().strip() == '':
            self.statuses[2] = 'ERROR: must enter values for both first name and last name'
            self.statusText.SetLabel('ERROR: must enter values for both first name and last name')
            self.button3.SetBackgroundColour('#C50202')
        else:
            self.statuses[2] = 'Waiting for result from server...'
            self.statusText.SetLabel('Waiting for result from server...')
            self.queries[2]=("SELECT * FROM PATIENT WHERE FNAME = '"+self.textCtrl1.GetValue().strip()
                             +"' AND LNAME = '"+self.textCtrl2.GetValue().strip()+"'")
            self.button3.SetBackgroundColour('#BD8000')
            self.executeRow.ShowItems(False)
            self.s.send('2|'+self.queries[2])

    def Query4(self, evt):
        if self.selected != 3:
            self.selected = 3
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[3])
            self.resultsText.SetLabel(self.results[3])
            if self.statuses[3].startswith('Waiting'):
                self.button4.SetBackgroundColour('#BD8000')
            else:
                if self.results[3].startswith('ERROR') or self.statuses[3].startswith('ERROR'):
                    self.button4.SetBackgroundColour('#C50202')
                    self.execute4 = wx.Button(self.topPanel, label="Re-Execute")
                    
                elif self.statuses[3].startswith('Displaying'):
                    self.button4.SetBackgroundColour('#229702')
                    self.execute4 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button4.SetBackgroundColour('#ABABAB')
                    self.execute4 = wx.Button(self.topPanel, label="Execute")
                self.executeRow.Add(self.execute4,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute4, self.execute4)
            self.Layout()
    def Execute4(self, evt):
        self.statuses[3] = 'Waiting for result from server...'
        self.statusText.SetLabel('Waiting for result from server...')
        self.queries[3]='SELECT * FROM PATIENT p INNER JOIN LOCATION l ON p.ADDRESS = l.ADDRESS'
        self.button4.SetBackgroundColour('#BD8000')
        self.executeRow.ShowItems(False)
        self.s.send('3|'+self.queries[3])

    def Query5(self, evt):
        if self.selected != 4:
            self.selected = 4
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[4])
            self.resultsText.SetLabel(self.results[4])
            if self.statuses[4].startswith('Waiting'):
                self.button5.SetBackgroundColour('#BD8000')
            else:
                if self.results[4].startswith('ERROR') or self.statuses[4].startswith('ERROR'):
                    self.button5.SetBackgroundColour('#C50202')
                    self.execute5 = wx.Button(self.topPanel, label="Re-Execute")
                    
                elif self.statuses[4].startswith('Displaying'):
                    self.button5.SetBackgroundColour('#229702')
                    self.execute5 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button5.SetBackgroundColour('#ABABAB')
                    self.execute5 = wx.Button(self.topPanel, label="Execute")
                self.executeRow.Add(self.execute5,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute5, self.execute5)
            self.Layout()
    def Execute5(self, evt):
        self.statuses[4] = 'Waiting for result from server...'
        self.statusText.SetLabel('Waiting for result from server...')
        self.queries[4]='SELECT * FROM LOCATION'
        self.button5.SetBackgroundColour('#BD8000')
        self.executeRow.ShowItems(False)
        self.s.send('4|'+self.queries[4])

    def Query6(self, evt):
        if self.selected != 5:
            self.selected = 5
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[5])
            self.resultsText.SetLabel(self.results[5])
            if self.statuses[5].startswith('Waiting'):
                self.button6.SetBackgroundColour('#BD8000')
            else:
                if self.results[5].startswith('ERROR') or self.statuses[5].startswith('ERROR'):
                    self.button6.SetBackgroundColour('#C50202')
                    self.execute6 = wx.Button(self.topPanel, label="Re-Execute")
                elif self.statuses[5].startswith('Displaying'):
                    self.button6.SetBackgroundColour('#229702')
                    self.execute6 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button6.SetBackgroundColour('#ABABAB')
                    self.execute6 = wx.Button(self.topPanel, label="Execute")
                self.textCtrl1 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.locationName = wx.StaticText(self.topPanel, label="Location name to delete:")
                self.executeRow.Add(self.locationName,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl1,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.execute6,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute6, self.execute6)
            self.Layout()
    def Execute6(self, evt):
        if self.textCtrl1.GetValue().strip() == '':
            self.statuses[5] = 'ERROR: must enter values for location name'
            self.statusText.SetLabel('ERROR: must enter values for location name')
            self.button6.SetBackgroundColour('#C50202')
        else:
            self.statuses[5] = 'Waiting for result from server...'
            self.statusText.SetLabel('Waiting for result from server...')
            self.queries[5]="DELETE FROM LOCATION WHERE NAME = '"+self.textCtrl1.GetValue().strip()+"'"
            self.button6.SetBackgroundColour('#BD8000')
            self.executeRow.ShowItems(False)
            self.s.send('5|'+self.queries[5])

    def Query7(self, evt):
        if self.selected != 6:
            self.selected = 6
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[6])
            self.resultsText.SetLabel(self.results[6])
            if self.statuses[6].startswith('Waiting'):
                self.button7.SetBackgroundColour('#BD8000')
            else:
                if self.results[6].startswith('ERROR') or self.statuses[6].startswith('ERROR'):
                    self.button7.SetBackgroundColour('#C50202')
                    self.execute7 = wx.Button(self.topPanel, label="Re-Execute")
                elif self.statuses[6].startswith('Displaying'):
                    self.button7.SetBackgroundColour('#229702')
                    self.execute7 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button7.SetBackgroundColour('#ABABAB')
                    self.execute7 = wx.Button(self.topPanel, label="Execute")
                self.textCtrl1 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.textCtrl2 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.textCtrl3 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.id = wx.StaticText(self.topPanel, label="ID: ")
                self.name = wx.StaticText(self.topPanel, label="Name: ")
                self.address = wx.StaticText(self.topPanel, label="Address: ")
                self.executeRow.Add(self.id,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl1,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.name,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl2,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.address,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl3,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.execute7,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute7, self.execute7)
            self.Layout()
    def Execute7(self, evt):
        if (self.textCtrl1.GetValue().strip() == '' or self.textCtrl2.GetValue().strip() == ''
                or self.textCtrl3.GetValue().strip() == ''):
            self.statuses[6] = 'ERROR: must enter values for location name'
            self.statusText.SetLabel('ERROR: must enter values for location name')
            self.button7.SetBackgroundColour('#C50202')
        else:
            self.statuses[6] = 'Waiting for result from server...'
            self.statusText.SetLabel('Waiting for result from server...')
            self.queries[6]=("INSERT INTO LOCATION(ID, NAME, ADDRESS) VALUES("+self.textCtrl1.GetValue().strip()+
                             ", '"+self.textCtrl2.GetValue().strip()+"', '"+self.textCtrl3.GetValue().strip()+"')")
            self.button7.SetBackgroundColour('#BD8000')
            self.executeRow.ShowItems(False)
            self.s.send('6|'+self.queries[6])

    def Query8(self, evt):
        if self.selected != 7:
            self.selected = 7
            self.ClearExecuteRowAndColor()
            self.statusText.SetLabel(self.statuses[7])
            self.resultsText.SetLabel(self.results[7])
            if self.statuses[7].startswith('Waiting'):
                self.button8.SetBackgroundColour('#BD8000')
            else:
                if self.results[7].startswith('ERROR') or self.statuses[7].startswith('ERROR'):
                    self.button8.SetBackgroundColour('#C50202')
                    self.execute8 = wx.Button(self.topPanel, label="Re-Execute")
                elif self.statuses[7].startswith('Displaying'):
                    self.button8.SetBackgroundColour('#229702')
                    self.execute8 = wx.Button(self.topPanel, label="Re-Execute")
                else:
                    self.button8.SetBackgroundColour('#ABABAB')
                    self.execute8 = wx.Button(self.topPanel, label="Execute")
                self.textCtrl1 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.textCtrl2 = wx.TextCtrl(self.topPanel, style=wx.TE_LEFT)
                self.oldname = wx.StaticText(self.topPanel, label="Old Location Name: ")
                self.newname = wx.StaticText(self.topPanel, label="New Location Name: ")
                self.executeRow.Add(self.oldname,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl1,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.newname,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM|wx.ALL,3)
                self.executeRow.Add(self.textCtrl2,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.executeRow.Add(self.execute8,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
                self.topPanel.Bind(wx.EVT_BUTTON, self.Execute8, self.execute8)
            self.Layout()
    def Execute8(self, evt):
        if self.textCtrl1.GetValue().strip() == '' or self.textCtrl2.GetValue().strip() == '':
            self.statuses[7] = 'ERROR: must enter values for location name'
            self.statusText.SetLabel('ERROR: must enter values for location name')
            self.button8.SetBackgroundColour('#C50202')
        else:
            self.statuses[7] = 'Waiting for result from server...'
            self.statusText.SetLabel('Waiting for server...')
            self.queries[7]=("UPDATE LOCATION SET NAME = '"+self.textCtrl2.GetValue().strip()+
                             "' WHERE NAME = '"+self.textCtrl1.GetValue().strip()+"'")
            self.button8.SetBackgroundColour('#BD8000')
            self.executeRow.ShowItems(False)
            self.s.send('7|'+self.queries[7])

    def ClearExecuteRowAndColor(self):
        for i in range(self.executeRow.GetItemCount())[::-1]:
            self.executeRow.Hide(i)
            self.executeRow.Remove(i)
            self.Layout()
        for i in range(8):
            color = self.getButton(i).GetBackgroundColour().GetAsString(wx.C2S_HTML_SYNTAX)
            if '#ABABAB' == color:
                self.getButton(i).SetBackgroundColour('#F0F0F0')#set to lighter gray
            elif '#BD8000' == color:
                self.getButton(i).SetBackgroundColour('#FFC20A')#set to lighter orange
            elif '#229702' == color:
                self.getButton(i).SetBackgroundColour('#31F000')#set to lighter green
            elif '#C50202' == color:
                self.getButton(i).SetBackgroundColour('#FF141E')#set to lighter red

    def getButton(self, num):
        if num<5:
            return self.queryButtons1.GetItem(num).GetWindow()
        else:
            return self.queryButtons2.GetItem(num-5).GetWindow()
            
    
#app = wx.App(False)
#To get errors use the following instead...
app = wx.App(True,'Error_Executor.txt')
frame = MyFrame()
frame.Show(True)

app.MainLoop()
