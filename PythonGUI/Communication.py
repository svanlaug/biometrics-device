
import Queue, threading, time, serial
from Globals            import *
from datetime import datetime


class ComMonitorThread(threading.Thread):
    """ A thread for monitoring a COM port. The COM port is 
        opened when the thread is started.
    
        data_q:
            Queue for received data. Items in the queue are
            (data, timestamp) pairs, where data is a binary 
            string representing the received data, and timestamp
            is the time elapsed from the thread's start (in 
            seconds).
        
        error_q:
            Queue for error messages. In particular, if the 
            serial port fails to open for some reason, an error
            is placed into this queue.
        
        port:
            The COM port to open. Must be recognized by the 
            system.
        
        port_baud/stopbits/parity: 
            Serial communication parameters
        
        port_timeout:
            The timeout used for reading the COM port. If this
            value is low, the thread will return data in finer
            grained chunks, with more accurate timestamps, but
            it will also consume more CPU.
    """
    def __init__(   self, 
                    data_q, error_q, 
                    port_num,
                    port_baud,
                    port_stopbits = serial.STOPBITS_ONE,
                    port_parity   = serial.PARITY_NONE,
                    port_timeout  = None):
        threading.Thread.__init__(self)
        
        self.serial_port = None
        self.serial_arg  = dict( port      = port_num,
                                 baudrate  = port_baud,
                                 stopbits  = port_stopbits,
                                 parity    = port_parity,
                                 timeout   = port_timeout)

        self.data_q   = data_q
        self.error_q  = error_q
        
        self.alive    = threading.Event()
        self.alive.set()
    #------------------------------------------------------



    #------------------------------------------------------

        
    def run(self):
        Temperature = 0;
        Beats = 0;
        BPM = 0;
        IBI = 0;
        GSR = 0;
        CycleTime = 0;
        Teljari = 0;

        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
        except serial.SerialException, e:
            self.error_q.put(e.message)
            return
        
        # Restart the clock
        startTime = time.time()
        
        while self.alive.isSet():
            #time.sleep(0.02)
            Line = self.serial_port.readline()
            if len(Line) > 1:

                if Line[0] == 'S':
                    Beats = float(Line[1:])
                if Line[0] == 'T':
                    Temperature = float(Line[1:])
                if Line[0] == 'B':
                    BPM = float(Line[1:])
                if Line[0] == 'Q':
                    IBI = float(Line[1:])
                if Line[0] == 'G':
                    GSR = float(Line[1:])
                if Line[0] == 'C':
                    CycleTime = float(Line[1:])
                if Line[0] == 'Y':
                    Teljari = float(Line[1:])

                qdata = [0,0,0,0,0,0,0,0]
                timestamp = time.time() - startTime
                qdata[0] = Beats
                qdata[1] = Temperature
                qdata[2] = GSR
                qdata[3] = BPM
                qdata[4] = IBI
                qdata[5] = CycleTime
                qdata[6] = Teljari
                now = datetime.now()
                qdata[7] = now.strftime("%H:%M:%S.%f")
                timestamp = time.clock()
                self.data_q.put((qdata, timestamp))
               
            
        # clean up
        if self.serial_port:
            self.serial_port.close()

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)

