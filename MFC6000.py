import RPi.GPIO as GPIO
import serial
import time
import struct
"""
CLASS for CONTROLLING SFC6000D( MFC stands for 'Mass Flow COntroller') using RS485 COM
(note that I2C is also available for SFC6000D but you should use RS485 ports).
Tested with Raspberry Pi 4 Model B attached with Waveshare RS485 CAN HAT.

"""
class MFC6000:
    #Raspberry Confıgs,INIT UART
    def __init__(self):
        self.EN_485 =  4
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.EN_485,GPIO.OUT)
        GPIO.output(self.EN_485,GPIO.HIGH)
        GPIO.setwarnings(False)
        self.t = serial.Serial("/dev/ttyS0",115200,timeout=1)

    #CREATE BYTES FRAME SPECIFIED IN THE DATASHEET
    def createFrame(self,CMD,TXDATA):
        PACKAGE=bytearray()
        ADR=0x0
        L=len(TXDATA)
        CHK=0xFF - ( (ADR+CMD+sum(TXDATA)+L) & 0xFF )
        PACKAGE.append(0x7E)
        PACKAGE.append(ADR)
        PACKAGE.append(CMD)
        PACKAGE.append(L)
        for i in TXDATA:
            PACKAGE.append(i)
        PACKAGE.append(CHK)
        PACKAGE.append(0x7E)
        return PACKAGE

#   SEND FRAME BYTES 
    def sendFrame(self,FRAME):
        if(self.t.isOpen()):
            self.t.write(FRAME)
        else:
            print("Open Serial First !")
#   READ FEEDBACK
    def ReadData(self,CMD):
        feedback=self.t.readall()
        if(feedback[0]==0x7e and feedback[1]==0x0 and feedback[2]==CMD and feedback[-1]==0x7e): #CHECK IF RETURNED DATA IS VALID
            data=[int(i) for i in feedback[5:-2]]
            print("\nFEEDBACK SUCCESFULLY READED!!!!!!\n")
        else:
            print("\nERROR ON READING FEEDBACK")
            print("FEEDBACK:",feedback,"\n")
            return type(feedback[0]) , feedback[1]==0x0 ,feedback[2]==CMD , feedback[-1]==0x7e #FIND PROBLEMATIC BYTE
        return data

# 	CONVERT BYTES TO STRING -MISO
    def BytestoString(self,Bytes):
        string=''.join(map(chr,Bytes))
        return string
    
# 	CONVERT BYTES TO FLOAT -MISO  
    def BytestoFloat(self,Bytes):
        byte_data=bytes(Bytes)
        floatdata=struct.unpack('f',byte_data)
        return floatdata
    
# 	CONVERT UINT BYTES TO INT -MISO  
    def UınttoInt(self,uınt):
        c=0
        ınt=0
        for i in list(uınt[::-1]):
            ınt+=i*(16**c)
            c+=2
        return ınt

# 	CONVERT FLOAT TO BYTES -MOSI          
    def FloattoBytes(self,Float):
        Floatbytes=struct.pack('f',Float)
        hex_values=[ int(byte) for byte in Floatbytes]
        return hex_values

# 	CONVERT INT TO UINT -MOSI     
    def InttoUınt(self,Int):
        byte_array=bytearray(Int.to_bytes((Int.bit_length()+7)//8,'big'))
        hexlist=[int(byte) for byte in byte_array]
        return hexlist
    
    def MeasureRawFlow(self):
        self.sendFrame(self.createFrame(0x30,[0x0]))
    
    def GetSetpoint(self):
        self.sendFrame(self.createFrame(0x00,[0x01]))
     
    def SetSetpoint(self,setpoint):
        hex_values=self.FloattoBytes(setpoint)
        self.sendFrame(self.createFrame(0x00,[0x01]+hex_values))
        
    def ReadMeasuredValue(self):
        self.sendFrame(self.createFrame(0x08,[0x01]))
        dmeasured=self.ReadData(0x08)
        measured=self.BytestoFloat(dmeasured)
        return measured
    
    def	ReadAveragedMeasuredValue(self,numavg):
        if(numavg<65536):
            self.sendFrame(self.createFrame(0x08,[0x11,numavg]))
        dmeasured=self.ReadData(0x08)
        measured=self.BytestoFloat(dmeasured)
        return measured
    
    def SetSetpointAndReadMeasuredValue(self,setpoint):
        hex_setpoint=self.FloattoBytes(setpoint)
        self.sendFrame(self.createFrame(0x03,[0x01]+hex_setpoint))
        dmeasured=self.ReadData(0x03)
        measured=self.BytestoFloat(dmeasured)
        return dmeasured
    
    def GetUserControllerGain(self):
        self.sendFrame(self.createFrame(0x22,[0x00]))
        bytegain=self.ReadData(0x22)
        gain=self.BytestoFloat(bytegain)
        return gain
    
    def SetUserControllerGain(self,ugain):
        hex_ugain=self.FloattoBytes(ugain)
        self.sendFrame(self.createFrame(0x22,[0x00]+hex_ugain))
    
    def GetUserInıtStep(self):
        self.sendFrame(self.createFrame(0x22,[0x03]))
        bytestep=self.ReadData(0x22)
        step=self.BytestoFloat(bytestep)
        return step
        
    def SetUserInıtStep(self,ıstep):
        hex_ıstep= self.FloattoBytes(ıstep)
        self.sendFrame(self.createFrame(0x22,[0x03]+hex_ıstep))
        
    def MeasureRawFlow(self):
        self.sendFrame(self.createFrame(0x30,[0x00]))
        byteflow=self.ReadData(0x30)
        return byteflow
    
    def MeasureRawThermalConductivityWithClosedValve(self):
        self.sendFrame(self.createFrame(0x30,[0x02]))
        byteconductivity=self.ReadData(0x30)
        conductivity=self.UınttoInt(byteconductivity)
        return conductivity       
    
    def MeasureTemperature(self):
        self.sendFrame(self.createFrame(0x30,[0x10]))
        byteconductivity=self.ReadData(0x30)
        conductivity=self.BytestoFloat(byteconductivity)
        return conductivity
    
    def GetNumberofCalibrations(self):
        self.sendFrame(self.createFrame(0x40,[0x00]))
        bytenumcalib=self.ReadData(0x40)
        numcalib=self.UınttoInt(bytenumcalib)
        return numcalib
    
    def GetCalibrationValidity(self,calibindex):
        hexcalibindex= self.FloattoBytes(ıstep)
        self.sendFrame(self.createFrame(0x40,[0x10]))
        pass
    
    def GetCalibrationGasId(self,CalIndex):
        CalIndexhex=self.InttoUınt(CalIndex)
        self.sendFrame(self.createFrame(0x40,[0x12]+CalIndexhex))
        IdByte=self.ReadData(0x40)
        Id=self.UınttoInt(IdByte)
        return IdByte
    
    def GetCalibrationGasUnıt(self):
        pass
    
    def GetCalibrationFullScale(self):
        pass
    
    def GetCurrentGasId(self):
        pass
    
    def GetCurrentgasUnıt(self):
        pass
    
    def GetCurrentFullScale(self):
        pass
    
    def GetCalibration(self):
        pass
    
    def SetCalibration(self,calibnum):
        pass
    
    def SetCalibrationVolatile(self,calibnum):
        pass
    
    def GetSlaveAddress(self):
        self.sendFrame(self.createFrame(0x90,[]))
        return self.ReadData(0x90)
        
    def SetSlaveAddress(self,uaddr):
        self.sendFrame(self.createFrame(0x90,[uaddr]))
        
    def GetBaudRate(self):
        self.sendFrame(self.createFrame(0x91,[]))
        uıntrate=self.ReadData(0x91)
        rate=self.UınttoInt(uıntrate)
        return rate
        
    def SetBaudRate(self,rate):
        hexrate=self.InttoUınt(rate)
        self.sendFrame(self.createFrame(0x91,[]+hexrate))        
        
    def GetProductType(self):
        self.sendFrame(self.createFrame(0xD0,[0x00]))
        bytestring=self.ReadData(0xD0)
        return self.BytestoString(bytestring)
    
    def GetProductName(self):
        self.sendFrame(self.createFrame(0xD0,[0x01]))
        bytestring=self.ReadData(0xD0)
        return self.BytestoString(bytestring)
    
    def GetArticleCode(self):
        self.sendFrame(self.createFrame(0xD0,[0x02]))
        bytestring=self.ReadData(0xD0)
        return self.BytestoString(bytestring)
    
    def GetSerialNumber(self):
        self.sendFrame(self.createFrame(0xD0,[0x03]))
        byteserial=self.ReadData(0xD0)
        return self.BytestoString(byteserial)
    
    def GetVersion(self):
        pass
    
    def DeviceReset(self):
        self.sendFrame(self.createFrame(0xD3,[]))
        
                

        
