
TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

class i2c:
    '''
    i2c class hierarchy
    -------------------

               ftdi_i2c
             /
         i2c
             \
               aardvark_i2c
             / (aardv.py)
    aardvark
    '''
    def enum (me): raise NotImplementedError()
    def baud (me, ask): raise NotImplementedError()
    def i2cw (me, wdat): raise NotImplementedError()
    def read (me, dev, adr, rcnt, rpt=FALSE): raise NotImplementedError()

    def write (me, dev, adr, wdat): # SMB write
        return me.i2cw ([dev,adr]+wdat)

    def probe (me):
        print 'Searching I2C slave.....'
        hit = []
        for dev in range(0x80):
            if me.i2cw ([dev]):
                print 'device 0x%02x found' % (dev)
                hit += [dev]
        return hit


CHOOSE_FTDI_FIRST = 1
CHOOSE_AARDVARK_FIRST = 2
def choose_master (order=CHOOSE_FTDI_FIRST, rpt=FALSE):
    '''
    TO CONSIDER FOLLOWING SCENARIOS
    -------------------------------
    1. use AARDARK in a non-Windows system
    2. use AARDARK in Windows without FTDI installed
    3. use FTDI in Windows without AARDARK installed
    4. use either AARDARK/FTDI in Windows with both installed
    '''
    from ftdi_i2c      import ftdi_i2c
    from cynpy.aardv   import aardvark_i2c as aard_i2c
    i2cmst = 0

    if order == CHOOSE_FTDI_FIRST:
        if ftdi_i2c().enum (rpt) > 0: i2cmst = ftdi_i2c(0)
        if not i2cmst and \
           aard_i2c().enum (rpt) > 0: i2cmst = aard_i2c(0)
            
    if order == CHOOSE_AARDVARK_FIRST:
        if aard_i2c().enum (rpt) > 0: i2cmst = aard_i2c(0)
        if not i2cmst and \
           ftdi_i2c().enum (rpt) > 0: i2cmst = ftdi_i2c(0)

    return i2cmst



if __name__ == '__main__':

    i2cmst = choose_master (rpt=TRUE)

    from cynpy.basic import *
    if not no_argument ():
        if i2cmst!=0:
            if   sys.argv[1]=='probe' : print i2cmst.probe ()
            elif sys.argv[1]=='baud'  : print i2cmst.baud (argv_dec[2])
            elif sys.argv[1]=='write' : print i2cmst.i2cw (argv_hex[2:])
            elif sys.argv[1]=='rdx'   : print ['0x%02X' % xx for xx in i2cmst.i2crx (argv_hex[2], argv_hex[3], argv_hex[4], FALSE)] # FTDI-only
            elif sys.argv[1]=='rdi'   : print ['0x%02X' % xx for xx in i2cmst.i2crx (argv_hex[2], argv_hex[3], argv_hex[4])] # FTDI-only
            elif sys.argv[1]=='read'  : print ['0x%02X' % xx for xx in i2cmst.read  (argv_hex[2], argv_hex[3], argv_hex[4])]
            else: print "command not recognized"
        else: print "I2C master not found"
