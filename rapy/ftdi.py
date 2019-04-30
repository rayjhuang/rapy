
TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

# FT others
FT_MAX_DESCRIPTION_SIZE = 256

class FT_STATUS:
    OK                          = 0
    INVALID_HANDLE              = 1
    DEVICE_NOT_FOUND            = 2
    DEVICE_NOT_OPENED           = 3
    IO_ERROR                    = 4
    INSUFFICIENT_RESOURCES      = 5
    INVALID_PARAMETER           = 6
    INVALID_BAUD_RATE           = 7
    DEVICE_NOT_OPENED_FOR_ERASE = 8
    DEVICE_NOT_OPENED_FOR_WRITE = 9
    FAILED_TO_WRITE_DEVICE      = 10
    EEPROM_READ_FAILED          = 11
    EEPROM_WRITE_FAILED         = 12
    EEPROM_ERASE_FAILED         = 13
    EEPROM_NOT_PRESENT          = 14
    EEPROM_NOT_PROGRAMMED       = 15
    INVALID_ARGS                = 16
    NOT_SUPPORTED               = 17
    OTHER_ERROR                 = 18

    def text (me,sta):
        if   sta == me.INVALID_HANDLE:              return 'FT_INVALID_HANDLE'
        elif sta == me.DEVICE_NOT_FOUND:            return 'FT_DEVICE_NOT_FOUND'
        elif sta == me.DEVICE_NOT_OPENED:           return 'FT_DEVICE_NOT_OPENED'
        elif sta == me.IO_ERROR:                    return 'FT_IO_ERROR'
        elif sta == me.INSUFFICIENT_RESOURCES:      return 'FT_INSUFFICIENT_RESOURCES'
        elif sta == me.INVALID_PARAMETER:           return 'FT_INVALID_PARAMETER'
        elif sta == me.INVALID_BAUD_RATE:           return 'FT_INVALID_BAUD_RATE'
        elif sta == me.DEVICE_NOT_OPENED_FOR_ERASE: return 'FT_DEVICE_NOT_OPENED_FOR_ERASE'
        elif sta == me.DEVICE_NOT_OPENED_FOR_WRITE: return 'FT_DEVICE_NOT_OPENED_FOR_WRITE'
        elif sta == me.FAILED_TO_WRITE_DEVICE:      return 'FT_FAILED_TO_WRITE_DEVICE'
        elif sta == me.EEPROM_READ_FAILED:          return 'FT_EEPROM_READ_FAILED'
        elif sta == me.EEPROM_WRITE_FAILED:         return 'FT_EEPROM_WRITE_FAILED'
        elif sta == me.EEPROM_ERASE_FAILED:         return 'FT_EEPROM_ERASE_FAILED'
        elif sta == me.EEPROM_NOT_PRESENT:          return 'FT_EEPROM_NOT_PRESENT'
        elif sta == me.EEPROM_NOT_PROGRAMMED:       return 'FT_EEPROM_NOT_PROGRAMMED'
        elif sta == me.INVALID_ARGS:                return 'FT_INVALID_ARGS'
        elif sta == me.NOT_SUPPORTED:               return 'FT_NOT_SUPPORTED'
        elif sta == me.OTHER_ERROR:                 return 'FT_OTHER_ERROR'
        elif sta == me.OK:                          return 'FT_OK'
        else:                                       return 'FT_UN_DEFINED'

class FT_DEVICE:
    FT232BM     = 0
    FT232AM     = 1
    FT100AX     = 2
    FT_UNKNOWN  = 3
    FT2232C     = 4
    FT232R      = 5
    FT2232H     = 6
    FT4232H     = 7
    FT232H      = 8
    FT_X_SERIES = 9

    def text (me,dev):
        if   dev == me.FT232BM:     return 'FT232BM'
        elif dev == me.FT232AM:     return 'FT232AM'
        elif dev == me.FT100AX:     return 'FT100AX'
        elif dev == me.FT_UNKNOWN:  return 'UNKNOWN'
        elif dev == me.FT2232C:     return 'FT2232C/L/D'
        elif dev == me.FT232R:      return 'FT232R'
        elif dev == me.FT2232H:     return 'FT2232H'
        elif dev == me.FT4232H:     return 'FT4232H'
        elif dev == me.FT232H:      return 'FT232H'
        elif dev == me.FT_X_SERIES: return 'FT_X_SERIES'
        else:                       return 'UNDEFINED'



import ctypes

class ftdi:
    def __init__ (me, dev=-1):
        me.lib = ctypes.windll.LoadLibrary("ftd2xx.dll")
        libVersion = ctypes.c_int()
        ret = me.lib.FT_GetLibraryVersion(ctypes.byref(libVersion))
        if ret != FT_STATUS.OK:
            print 'FT_GetLibraryVersion failed, %s' % FT_STATUS().text(ret)
        else:
            print 'FTD2XX LibraryVersion: 0x%08x' % (libVersion.value)

        me.handle = ctypes.c_int()
        if dev>= 0:
            me.openChannel (dev)

    def openChannel (me,idx):
        ret = me.lib.FT_Open(idx,ctypes.byref(me.handle))
        if ret != FT_STATUS.OK:
            print 'FT_Open failed, %s' % FT_STATUS().text(ret)
        else:
            print 'Open: 0x%08x' % (me.handle.value)

            driverVersion = ctypes.c_int()
            ret = me.lib.FT_GetDriverVersion(me.handle,ctypes.byref(driverVersion))
            if ret != FT_STATUS.OK:
                print 'FT_GetDriverVersion failed, %s' % FT_STATUS().text(ret)
            else:
                print 'DriverVersion: 0x%08x' % (driverVersion.value)

                deviceType = ctypes.c_int()
                deviceId   = ctypes.c_int()
                desc       = ctypes.c_buffer(FT_MAX_DESCRIPTION_SIZE)
                serial     = ctypes.c_buffer(FT_MAX_DESCRIPTION_SIZE/4)
                ret = me.lib.FT_GetDeviceInfo(me.handle,
                                        ctypes.byref(deviceType),
                                        ctypes.byref(deviceId), serial, desc, None)
                if ret != FT_STATUS.OK:
                    print 'GetDeviceInfo failed, %s' % FT_STATUS.text(ret)
                else:
                    print 'device: %s\nvid/pid: 0x%08X\nserial: %s\n%s' % \
                                          (FT_DEVICE().text(deviceType.value),
                                           deviceId.value,serial.value,desc.value)

    def enum (me):
            numDev = ctypes.c_int()
            ret = me.lib.FT_CreateDeviceInfoList(ctypes.byref(numDev))
            if ret != FT_STATUS.OK:
                print 'FT_CreateDeviceInfoList failed, %s' % FT_STATUS().text(ret)
            else:
                print '%d FTD2XX Device(s) found' % (numDev.value)

                for idx in reversed(range(numDev.value)):
                    print '%s\nDEVICE %d\n%s' % ('-'*10,idx,'v'*10)

                    me.openChannel (idx)

                    FT_NumComs = ctypes.c_int()
                    ret = me.lib.FT_GetComPortNumber(me.handle,ctypes.byref(FT_NumComs))
                    if ret != FT_STATUS.OK:
                        print 'FT_GetComPortNumber failed, %s' % FT_STATUS().text(ret)
                    elif FT_NumComs.value < 0:
                        print 'no serial port'
                    else:
                        print 'serial port on COM%d' % (FT_NumComs.value)

                        ret = me.lib.FT_SetBaudRate(me.handle,28800)
                        if ret != FT_STATUS.OK:
                            print 'FT_SetBaudRate failed, %s' % FT_STATUS().text(ret)
                        else:
                            print 'set baudrate 28800'



if __name__ == '__main__':

    def test_only ():
        pass

    from cynpy.basic import *
    if not no_argument ():
        if   sys.argv[1]=='enum' : ftdi().enum ()
        elif sys.argv[1]=='test' : test_only  ()
        else: print "command not recognized"
