
from rapy.ftdi import FT_STATUS, TRUE, FALSE, FT_MAX_DESCRIPTION_SIZE
import ctypes

class ChannelConfig(ctypes.Structure):
    _fields_ = [("ClockRate",   ctypes.c_int),   # 0~3,400,000
                ("LatencyTimer",ctypes.c_ubyte), # uint8
                ("Options",     ctypes.c_int)]   # uint32

class I2C_CONFIG_OPTION:
    DISABLE_3PHASE_CLOCKING = 0x00000001
    ENABLE_DRIVE_ONLY_ZERO  = 0x00000002

class I2C_CLOCKRATE:
    STANDARD_MODE       = 100000
    STANDARD_MODE_PLUS  = 200000
    FAST_MODE           = 400000
    FAST_MODE_PLUS      = 1000000
    HIGH_SPEED_MODE     = 3400000

class I2C_TRANSFER_OPTION:
    START_BIT           = 0x01
    STOP_BIT            = 0x02
    BREAK_ON_NACK       = 0x04
    NACK_LAST_BYTE      = 0x08
    FAST_TRANSFER_BYTES = 0x10
    FAST_TRANSFER_BITS  = 0x20
    FAST_TRANSFER       = 0x30
    NO_ADDRESS          = 0x40



from rapy.i2c import i2c

class ftdi_i2c (i2c):
    def __init__ (me, dev=-1):
        me.handle = ctypes.c_int()
        me.nbytes = ctypes.c_int() # bytes_transfered
        me.buffer = ctypes.create_string_buffer(FT_MAX_DESCRIPTION_SIZE)
        try:
            me.lib = ctypes.cdll.LoadLibrary("libMPSSE.dll")
            me.lib.Init_libMPSSE()
            if dev >= 0:
                me.openChannel (dev)
        except:
            me.lib = 0


    def __del__ (me):
        if me.handle.value:
            ret = me.lib.I2C_CloseChannel(me.handle)
            if FT_STATUS.OK != ret:
                print 'I2C_CloseChannel status:', FT_STATUS().text(ret)

        if me.lib:
            me.lib.Cleanup_libMPSSE()


    def openChannel (me, idx):
        if me.lib:
            ret = me.lib.I2C_OpenChannel(idx, ctypes.byref(me.handle))
            if FT_STATUS.OK != ret:
                print 'I2C_OpenChannel failed, %s' % FT_STATUS().text(ret)
            else:
#              print 'I2C on channel %d handle: 0x%08x' % (idx, me.handle.value)

                chn_conf = ChannelConfig(I2C_CLOCKRATE.STANDARD_MODE_PLUS,
                                         1, # latency
#                                        0)
                                         I2C_CONFIG_OPTION.DISABLE_3PHASE_CLOCKING | \
                                         I2C_CONFIG_OPTION.ENABLE_DRIVE_ONLY_ZERO)

                ret = me.lib.I2C_InitChannel(me.handle,ctypes.byref(chn_conf))
                if FT_STATUS.OK != ret:
                    print 'I2C_InitChannel failed, %s' % FT_STATUS().text(ret)

                 # the 1st I2C_DeviceWrite() is broken, drop it
                ret = me.lib.I2C_DeviceWrite(me.handle, 0, 0, me.buffer,
                                                 ctypes.byref(me.nbytes),
                                                 I2C_TRANSFER_OPTION.STOP_BIT)


    def enum (me, rpt=FALSE):
        chn_count = ctypes.c_int()
        if me.lib:
            ret = me.lib.I2C_GetNumChannels(ctypes.byref(chn_count))
            if rpt:
                if FT_STATUS.OK != ret:
                    print 'I2C_GetNumChannels failed, %s' % FT_STATUS().text(ret)
                else:
                    print '%d FTDI I2C channel(s) found' % chn_count.value

                    for idx in reversed(range(chn_count.value)):
                        print '%s\nI2C DEVICE %d\n%s' % ('-'*10,idx,'v'*10)

#                       me.openChannel (idx)

            return chn_count.value
        else:
            return 0


    def i2cr1 (me, dev, adr, rpt=FALSE): # single read
        assert me.handle > 0, 'no FDTI I2C device opened'
        me.buffer[0] = chr(adr)
        mode = I2C_TRANSFER_OPTION.START_BIT | \
               I2C_TRANSFER_OPTION.STOP_BIT | \
               I2C_TRANSFER_OPTION.FAST_TRANSFER_BYTES
        ret = me.lib.I2C_DeviceWrite(me.handle, dev, 1, me.buffer,
                                             ctypes.byref(me.nbytes), mode)
        assert FT_STATUS.OK == ret, \
            '0x%02x I2C_DeviceWrite failed, %s' % (adr, FT_STATUS().text(ret))

        mode = I2C_TRANSFER_OPTION.START_BIT | \
               I2C_TRANSFER_OPTION.NACK_LAST_BYTE
        ret = me.lib.I2C_DeviceRead(me.handle, dev, 1, me.buffer,
                                             ctypes.byref(me.nbytes), mode)
        assert FT_STATUS.OK == ret, \
            '0x%02x I2C_DeviceRead failed, %s' % (adr, FT_STATUS().text(ret))

        assert me.nbytes.value == 1, 'byte-read error, %d' % (me.nbytes.value)
        return ord(me.buffer[0])


    def i2crx (me, dev, adr, bycnt, i2cr1i=TRUE, rpt=FALSE): # SMB read
        '''
        when can not burst read because of the glitch during ACK/NCK bit
        i2cr1i is used when invoke i2cr1 to emulate burst read
        '''
        ret = []
        for xx in range(bycnt):
            ret += [me.i2cr1 (dev, adr+(xx if i2cr1i==TRUE else 0), rpt)]
        return ret


    def read (me, dev, adr, bycnt, rpt=FALSE): # SMB read
        '''
        note the glitch during ACK/NCK bit
        carefully trim the bridge freq.<12MHz
        '''
        assert me.handle > 0, 'no FDTI I2C device opened'
        me.buffer[0] = chr(adr)
        mode = I2C_TRANSFER_OPTION.START_BIT | \
               I2C_TRANSFER_OPTION.STOP_BIT | \
               I2C_TRANSFER_OPTION.FAST_TRANSFER_BYTES
        ret = me.lib.I2C_DeviceWrite(me.handle, dev, 1, me.buffer,
                                             ctypes.byref(me.nbytes), mode)
        assert FT_STATUS.OK == ret, \
            '0x%02x I2C_DeviceWrite failed, %s' % (adr, FT_STATUS().text(ret))

        mode = I2C_TRANSFER_OPTION.START_BIT | \
               I2C_TRANSFER_OPTION.NACK_LAST_BYTE
#              I2C_TRANSFER_OPTION.FAST_TRANSFER_BYTES | \
#              I2C_TRANSFER_OPTION.STOP_BIT | \
        ret = me.lib.I2C_DeviceRead(me.handle, dev, bycnt, me.buffer,
                                             ctypes.byref(me.nbytes), mode)
        assert FT_STATUS.OK == ret, \
            '0x%02x I2C_DeviceRead failed, %s' % (adr, FT_STATUS().text(ret))
        if rpt:
            print '0x%02x, %d byte(s) read' % (adr, me.nbytes.value)

        ret = []
        for xx in me.buffer[0:me.nbytes.value]:
            ret += [ord(xx)]
        assert len(ret) == bycnt, 'read byte-count error, cnt:%d, exp:%d' % (len(ret),me.nbytes.value)
        return ret


    def i2cw (me, wdat, rpt=FALSE): # I2C write
        assert me.handle.value > 0, 'no FTDI I2C device opened'
        assert len(wdat) > 0, 'empty write data is not valid'
        for xx in range(len(wdat)-1):
            assert wdat[xx+1] < 256, 'write data is not in byte'
            me.buffer[xx] = chr(wdat[xx+1])
        mode = I2C_TRANSFER_OPTION.START_BIT | \
               I2C_TRANSFER_OPTION.STOP_BIT

        if len(wdat) > 1:
            mode |= I2C_TRANSFER_OPTION.FAST_TRANSFER_BYTES

        ret = me.lib.I2C_DeviceWrite(me.handle, wdat[0], len(wdat)-1, me.buffer,
                                             ctypes.byref(me.nbytes), mode)
        if FT_STATUS.OK != ret:
            if rpt:
                print '0x%02x I2C_DeviceWrite failed, %s' % (wdat[0], FT_STATUS().text(ret))
            return 0
        else:
            if rpt:
                print '0x%02x, %d byte(s) transfered' % (wdat[0], me.nbytes.value)
            return me.nbytes.value + 1



if __name__ == '__main__':

    def test_only ():
        i2c = ftdi_i2c(0)
        yy = 0
        for xx in range(1000):
            yy += i2c.i2cw ([0x3c])
        print yy

    from cynpy.basic import *
    if not no_argument ():
        if   sys.argv[1]=='enum'  : ftdi_i2c().enum (rpt=TRUE)
        elif sys.argv[1]=='probe' : ftdi_i2c(0).probe ()
        elif sys.argv[1]=='read'  : ftdi_i2c(0).read (argv_hex[2], argv_hex[3], 1)
        elif sys.argv[1]=='test'  : test_only ()
        else: print "command not recognized"

