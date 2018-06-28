#!/usr/bin/python
# -*- coding: cp1252 -*-

import  random, sys, Queue, serial, glob, os, csv, time

import  PyQt4.Qwt5     as Qwt
from    PyQt4.QtCore   import *
from    PyQt4.QtGui    import *

from Communication        import ComMonitorThread
from Globals            import *
from datetime import datetime


class AtmelPythonPlot(QMainWindow):
    def __init__(self, parent=None):
        super(AtmelPythonPlot, self).__init__(parent)

        self.setWindowTitle("Svana's Biometrics")
        self.resize(1024, 800)
        
        self.port           = ""
        self.baudrate       = 19200
        self.monitor_active = False
        self.com_monitor    = None
        self.com_data_q     = None
        self.com_error_q    = None
        self.livefeed       = LiveDataFeed()
        self.timer          = QTimer()
        self.g_samples      = [[], [], []]
        self.curve          = [None]*3
        self.gcurveOn       = [1]*3
        self.csvdata        = []
        self.BPM            = 0
        self.PushButtonNew  = 0
        self.PushButtonOld  = 0
        
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        # Activate start-stop button connections
        self.connect(self.button_Connect, SIGNAL("clicked()"),
                    self.OnStart)
        self.connect(self.button_Disconnect, SIGNAL("clicked()"),
                    self.OnStop)
        self.connect(self.button_Increment, SIGNAL("clicked()"),
                    self.Increment)

    #----------------------------------------------------------


    def create_com_box(self):
        self.com_box = QGroupBox("COM Configuration")

        com_layout = QGridLayout()

        self.radio9600     =    QRadioButton("9600")
        self.radio19200    =    QRadioButton("19200")
        self.radio19200.setChecked(1)
        self.Com_ComboBox  =    QComboBox()

        com_layout.addWidget(self.Com_ComboBox,0,0,1,2)
        com_layout.addWidget(self.radio9600,1,0)
        com_layout.addWidget(self.radio19200,1,1)
        self.fill_ports_combobox()

        self.button_Connect      =   QPushButton("Start")
        self.button_Disconnect   =   QPushButton("Stop")
        self.button_Disconnect.setEnabled(False)

        self.button_Increment      =   QPushButton("Increment")

        com_layout.addWidget(self.button_Connect,0,2)
        com_layout.addWidget(self.button_Disconnect,1,2)
        com_layout.addWidget(self.button_Increment,2,2)

        return com_layout
    #---------------------------------------------------------------------
   

    def create_plot(self):
        self.Trigger1 = 0;
        self.MaxSamplesPlot1 = 6000
        plot = Qwt.QwtPlot(self)
        plot.setCanvasBackground(Qt.black)
        plot.setAxisTitle(Qwt.QwtPlot.xBottom, '')
        plot.setAxisScale(Qwt.QwtPlot.xBottom, 0, 20, 5)
        plot.setAxisTitle(Qwt.QwtPlot.yLeft, 'Heart Rhythm [Raw Value]')
        plot.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        plot.replot()
        
        curve = [None]*3
        pen = [QPen(QColor('limegreen')), QPen(QColor('red')) ,QPen(QColor('magenta')) ]
        for i in range(3):
            curve[i] =  Qwt.QwtPlotCurve('')
            curve[i].setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
            pen[i].setWidth(2)
            curve[i].setPen(pen[i])
            curve[i].attach(plot)

        return plot, curve
    #---------------------------------------------------

    def create_plot2(self):
        self.Trigger2 = 0;
        self.MaxSamplesPlot2 = 6000
        plot2 = Qwt.QwtPlot(self)
        plot2.setCanvasBackground(Qt.black)
        plot2.setAxisTitle(Qwt.QwtPlot.xBottom, '')
        plot2.setAxisScale(Qwt.QwtPlot.xBottom, 0, 60, 5)
        plot2.setAxisTitle(Qwt.QwtPlot.yLeft, 'Temperature [degC]')
        plot2.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        plot2.replot()

        curve2 = [None]*3
        pen = [QPen(QColor('limegreen')), QPen(QColor('red')) ,QPen(QColor('magenta')) ]
        for i in range(3):
            curve2[i] =  Qwt.QwtPlotCurve('')
            curve2[i].setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
            pen[i].setWidth(2)
            curve2[i].setPen(pen[i])
            curve2[i].attach(plot2)

        return plot2, curve2

    def create_plot3(self):
        self.Trigger3 = 0;
        self.MaxSamplesPlot3 = 6000
        plot3 = Qwt.QwtPlot(self)
        plot3.setCanvasBackground(Qt.black)
        plot3.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        plot3.setAxisScale(Qwt.QwtPlot.xBottom, 0, 60, 5)
        plot3.setAxisTitle(Qwt.QwtPlot.yLeft, 'GSR [Raw Value]')
        plot3.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        plot3.replot()

        curve3 = [None]*3
        pen = [QPen(QColor('limegreen')), QPen(QColor('red')) ,QPen(QColor('magenta')) ]
        for i in range(3):
            curve3[i] =  Qwt.QwtPlotCurve('')
            curve3[i].setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
            pen[i].setWidth(2)
            curve3[i].setPen(pen[i])
            curve3[i].attach(plot3)

        return plot3, curve3

    def create_knob(self):
        knob = Qwt.QwtKnob(self)
        knob.setRange(0, 180, 0, 1)
        knob.setScaleMaxMajor(10)
        knob.setKnobWidth(50)
        knob.setValue(100)
        return knob
    #---------------------------------------------------


    def create_status_bar(self):
        self.status_text = QLabel('Monitor idle')
        self.statusBar().addWidget(self.status_text, 1)
    #---------------------------------------------------


    def create_checkbox(self, label, color, connect_fn, connect_param):
        checkBox = QCheckBox(label)
        checkBox.setChecked(1)
        checkBox.setFont( QFont("Arial", pointSize=12, weight=QFont.Bold ) )
        green = QPalette()
        green.setColor(QPalette.Foreground, color)
        checkBox.setPalette(green)
        self.connect(checkBox, SIGNAL("clicked()"), partial(connect_fn,connect_param))
        return checkBox
        #---------------------------------------------------


    def create_main_frame(self):
        portname_layout = self.create_com_box()
        self.com_box.setLayout(portname_layout)
        
        # Update speed knob
        self.updatespeed_knob = self.create_knob()
        self.connect(self.updatespeed_knob, SIGNAL('valueChanged(double)'),
            self.on_knob_change)
        self.knob_l = QLabel('Update speed = %s (Hz)' % self.updatespeed_knob.value())
        self.knob_l.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Create the plot and curves
        self.plot, self.curve = self.create_plot()
        self.plot2, self.curve2 = self.create_plot2()
        self.plot3, self.curve3 = self.create_plot3()

        # Create the configuration horizontal panel
        self.max_spin    = QSpinBox()
        self.max_spin.setMaximum(100000)
        self.max_spin.setValue(25000)
        spins_hbox      = QHBoxLayout()
        spins_hbox.addWidget(QLabel('Save every'))
        spins_hbox.addWidget(self.max_spin)
        spins_hbox.addWidget( QLabel('Lines'))

        self.BPMscreen = QLabel('  BPM: ')
        self.IBIscreen = QLabel('  IBI: ')
        self.TemperatureScreen = QLabel('  Temp: ')
        self.PushButtonScreen = QLabel('  Measurement # ')
        self.Memory = QLabel('  CSV Memory: ')


        self.gCheckBox   =  [   self.create_checkbox("Heart Rhythm", Qt.green, self.activate_curve, 0),
                                self.create_checkbox("Temperature °C", Qt.red, self.activate_curve, 1),
                                self.create_checkbox("GSR", Qt.magenta, self.activate_curve, 2)
                            ]

        self.button_clear      =   QPushButton("Clear screen")

        self.connect(self.button_clear, SIGNAL("clicked()"),
                    self.clear_screen)
        
        # Place the horizontal panel widget
        plot_layout = QGridLayout()
        plot_layout.addWidget(self.plot,0,0,8,7)
        plot_layout.addWidget(self.plot2,10,0,8,7)
        plot_layout.addWidget(self.plot3,20,0,8,7)
        plot_layout.addWidget(self.gCheckBox[0],0,8)
        plot_layout.addWidget(self.gCheckBox[1],1,8)
        plot_layout.addWidget(self.gCheckBox[2],2,8)
        plot_layout.addWidget(self.button_clear,3,8)
        plot_layout.addLayout(spins_hbox,4,8)
        plot_layout.addWidget(self.updatespeed_knob,5,8)
        plot_layout.addWidget(self.knob_l,6,8)
        plot_layout.addWidget(self.BPMscreen,10,8)
        plot_layout.addWidget(self.IBIscreen,11,8)
        plot_layout.addWidget(self.TemperatureScreen,12,8)
        plot_layout.addWidget(self.PushButtonScreen,13,8)
        plot_layout.addWidget(self.Memory,14,8)

        plot_groupbox = QGroupBox('')
        plot_groupbox.setLayout(plot_layout)
        
        # Place the main frame and layout
        self.main_frame = QWidget()
        main_layout 	= QVBoxLayout()
        main_layout.addWidget(self.com_box)
        main_layout.addWidget(plot_groupbox)
        main_layout.addStretch(1)
        self.main_frame.setLayout(main_layout)
        self.setCentralWidget(self.main_frame)
    #----------------------------------------------------------------------


    def clear_screen(self):
        for i in range(3):
                self.g_samples[i] = []
    #-----------------------------
        

    def activate_curve(self, axe):
        if self.gCheckBox[axe].isChecked():
            self.gcurveOn[axe]  = 1
        else:
            self.gcurveOn[axe]  = 0
    #---------------------------------------


    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")
        
        selectport_action = self.create_action("Select COM &Port...",
            shortcut="Ctrl+P", slot=self.on_select_port, tip="Select a COM port")
        self.start_action = self.create_action("&Start monitor",
            shortcut="Ctrl+M", slot=self.OnStart, tip="Start the data monitor")
        self.stop_action = self.create_action("&Stop monitor",
            shortcut="Ctrl+T", slot=self.OnStop, tip="Stop the data monitor")
        exit_action = self.create_action("E&xit", slot=self.close, 
            shortcut="Ctrl+X", tip="Exit the application")
        
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(False)
        
        self.add_actions(self.file_menu, 
            (   selectport_action, self.start_action, self.stop_action,
                None, exit_action))
            
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About the monitor')
        
        self.add_actions(self.help_menu, (about_action,))
    #----------------------------------------------------------------------


    def set_actions_enable_state(self):
        if self.portname.text() == '':
            start_enable = stop_enable = False
        else:
            start_enable = not self.monitor_active
            stop_enable = self.monitor_active
        
        self.start_action.setEnabled(start_enable)
        self.stop_action.setEnabled(stop_enable)
    #-----------------------------------------------


    def on_about(self):
        msg = __doc__
        QMessageBox.about(self, "About the demo", msg.strip())
    #-----------------------------------------------

    

    def on_select_port(self):
        
        ports = enumerate_serial_ports()
        
        if len(ports) == 0:
            QMessageBox.critical(self, 'No ports',
                'No serial ports found')
            return
        
        item, ok = QInputDialog.getItem(self, 'Select a port',
                    'Serial port:', ports, 0, False)
        
        if ok and not item.isEmpty():
            self.portname.setText(item)            
            self.set_actions_enable_state()
    #-----------------------------------------------


    def fill_ports_combobox(self):
        vNbCombo = ""
        self.Com_ComboBox.clear()
        self.AvailablePorts = enumerate_serial_ports()
        for value in self.AvailablePorts:
            self.Com_ComboBox.addItem(value)
            vNbCombo += value + " - "
        vNbCombo = vNbCombo[:-3] 

    #----------------------------------------------------------------------


    def OnStart(self):
        """ Start the monitor: com_monitor thread and the update timer     
        """
        if self.radio19200.isChecked():
            self.baudrate = 19200
            print "--> baudrate is 19200 bps"
        if self.radio9600.isChecked():
            self.baudrate = 9600
            print "--> baudrate is 9600 bps"  

        vNbCombo    = self.Com_ComboBox.currentIndex()
        self.port   = self.AvailablePorts[vNbCombo]

        self.button_Connect.setEnabled(False)
        self.button_Disconnect.setEnabled(True)
        self.Com_ComboBox.setEnabled(False)

        self.data_q      =  Queue.Queue()
        self.error_q     =  Queue.Queue()
        self.com_monitor =  ComMonitorThread(
                                            self.data_q,
                                            self.error_q,
                                            self.port,
                                            self.baudrate)
        
        self.com_monitor.start()  

        com_error = get_item_from_queue(self.error_q)
        if com_error is not None:
            QMessageBox.critical(self, 'ComMonitorThread error',
                com_error)
            self.com_monitor = None  

        self.monitor_active = True

        self.connect(self.timer, SIGNAL('timeout()'), self.on_timer)
        
        update_freq = self.updatespeed_knob.value()
        if update_freq > 0:
            self.timer.start(1000.0 / update_freq)
        
        self.status_text.setText('Monitor running')
        debug('--> Monitor running')
    #------------------------------------------------------------


    def Increment(self):
        print self.PushButtonNew
        self.PushButtonNew = self.PushButtonNew + 1
        print self.PushButtonNew


    def OnStop(self):
        """ Stop the monitor
        """
        if self.com_monitor is not None:
            self.com_monitor.join(1000)
            self.com_monitor = None

        self.monitor_active = False
        self.button_Connect.setEnabled(True)
        self.button_Disconnect.setEnabled(False)
        self.Com_ComboBox.setEnabled(True)
        self.timer.stop()
        self.status_text.setText('Monitor idle')
        debug('--> Monitor idle')
    #-----------------------------------------------


    def on_timer(self):
        """ Executed periodically when the monitor update timer
            is fired.
        """
        self.read_serial_data()
        self.update_monitor()
	#-----------------------------------------------


    def on_knob_change(self):
        """ When the knob is rotated, it sets the update interval
            of the timer.
        """
        update_freq = self.updatespeed_knob.value()
        self.knob_l.setText('Update speed = %s (Hz)' % self.updatespeed_knob.value())
        if self.timer.isActive():
            update_freq = max(0.01, update_freq)
            self.timer.setInterval(1000.0 / update_freq)
    #-----------------------------------------------


    def update_monitor(self):
        if self.livefeed.has_new_data:
            data = self.livefeed.read_data()

            self.csvdata.append([data['dateTime'], self.PushButtonNew, data['rawBeats'], data['temp'], data['GSR'], data['BPM'], data['IBI'] ] )
            if len(self.csvdata) > self.max_spin.value() or self.PushButtonNew != self.PushButtonOld:
                if self.PushButtonNew != self.PushButtonOld:
                    self.PushButtonOld = self.PushButtonNew

                now = datetime.now()
                f = open(now.strftime("%H%M%S%f")+".csv", 'wt')
                try:
                    writer = csv.writer(f, delimiter=";")
                    for i in range(len(self.csvdata)):
                        writer.writerow( self.csvdata[i] )
                    print 'Data written to CSV file'
                finally:
                    f.close()
                self.csvdata = []
            
            self.g_samples[0].append(
                (data['timestamp'], data['rawBeats']))
            if len(self.g_samples[0]) > self.MaxSamplesPlot1:
                self.g_samples[0].pop(0)

            self.g_samples[1].append(
                (data['timestamp'], data['temp']))
            if len(self.g_samples[1]) > self.MaxSamplesPlot2:
                self.g_samples[1].pop(0)

            self.g_samples[2].append(
                (data['timestamp'], data['GSR']))
            if len(self.g_samples[2]) > self.MaxSamplesPlot3:
                self.g_samples[2].pop(0)

            tdata1 = [s[0] for s in self.g_samples[0]]
            tdata2 = [s[0] for s in self.g_samples[1]]
            tdata3 = [s[0] for s in self.g_samples[2]]

            for i in range(3):
                data[i] = [s[1] for s in self.g_samples[i]]

            if self.gcurveOn[0]:
                self.curve[0].setData(tdata1, data[0])
            if self.gcurveOn[1]:
                self.curve2[1].setData(tdata2, data[1])
            if self.gcurveOn[2]:
                self.curve3[2].setData(tdata3, data[2])

            self.plot.setAxisScale(Qwt.QwtPlot.xBottom, tdata1[0], max(10, tdata1[-1]) )
            self.plot2.setAxisScale(Qwt.QwtPlot.xBottom, tdata2[0], max(60, tdata2[-1]) )
            self.plot3.setAxisScale(Qwt.QwtPlot.xBottom, tdata3[0], max(60, tdata3[-1]) )

            if tdata1[-1]>20 and self.Trigger1 == 0:
                self.MaxSamplesPlot1 = len(self.g_samples[0])
                self.Trigger1 = 1

            if tdata2[-1]>60 and self.Trigger2 == 0:
                self.MaxSamplesPlot2 = len(self.g_samples[1])
                self.Trigger2 = 1

            if tdata3[-1]>60 and self.Trigger3 == 0:
                self.MaxSamplesPlot3 = len(self.g_samples[2])
                self.Trigger3 = 1

            self.plot.replot()
            self.plot2.replot()
            self.plot3.replot()

            self.BPMscreen.setText('  BPM = %d' % self.BPM)
            self.IBIscreen.setText('  IBI = %d' % self.IBI)
            self.TemperatureScreen.setText('  Temp = %.2f' % self.Temp)
            self.PushButtonScreen.setText('  Measurement # %d' % self.PushButtonNew)
            lengd = len(self.csvdata)
            maxSpins = self.max_spin.value()
            percentage = float(lengd)/float(maxSpins)*100
            self.Memory.setText('  CSV Memory %d %%' % percentage)

    #-----------------------------------------------
            
            
    def read_serial_data(self):
        """ Called periodically by the update timer to read data
            from the serial port.
        """
        qdata = list(get_all_from_queue(self.data_q))
        # get just the most recent data, others are lost

        if len(qdata) > 0:
            data = dict(timestamp=qdata[-1][1],
                        rawBeats=qdata[-1][0][0],
                        temp=qdata[-1][0][1],
                        GSR=qdata[-1][0][2],
                        BPM=qdata[-1][0][3],
                        IBI=qdata[-1][0][4],
                        CycleTime=qdata[-1][0][5],
                        Teljari=qdata[-1][0][6],
                        dateTime=qdata[-1][0][7]
                        )
            self.BPM = qdata[-1][0][3]
            self.IBI = qdata[-1][0][4]
            self.Temp = qdata[-1][0][1]
            #self.PushButtonNew = qdata[-1][0][6]
            self.livefeed.add_data(data)

            #print data
    #-----------------------------------------------


    
    # The following two methods are utilities for simpler creation
    # and assignment of actions
    #
    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    #-----------------------------------------------


    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
    #-----------------------------------------------

    

def main():
    app = QApplication(sys.argv)
    form = AtmelPythonPlot()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
    