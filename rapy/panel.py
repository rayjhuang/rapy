
TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

class cursor (object):
    def __init__ (me, height, width, show=FALSE):
        me.height = height
        me.width = width
        me.show = show
        me.reset()

    def reset (me):
        me.row = 0
        me.col = 0

    def line_feed (me):
        '''
        return TRUE if need scroll
        '''
        me.row += 1
        if me.row < me.height:
            return FALSE
        else:
            me.row -= 1
            return TRUE

    def move_right (me, wrap):
        '''
        move right, no wrap, stop out of bondary
        return (TRUE/FLASE, TRUE/FALSE) to indicate (scroll, line feed)
        '''
        me.col += 1
        if me.col < me.width:
            return (FALSE, FALSE)
        else:
            me.col = 0
            return (me.line_feed (), TRUE)

    def move_left (me):
        '''
        move left, don't change row, stop at col 0
        '''
        if me.col > 0:
            me.col -= 1
       
        

from font import font8x8

class text_frame (object):
    '''
               sh1106 {busmst
              /
    text_frame
    {font     \
    {buffer    other_panel {busmst
    {cursor
    '''
    WIDTH = 128
    HEIGHT = 64
    PAGE = 8 # 8-line / page, = font_sizes

    def __init__ (me, font):
        me.ox = 0
        me.oy = 0
        me.sz = me.PAGE
        me.buffer = [0] * (me.WIDTH *me.HEIGHT *me.PAGE)
        me.cursor = cursor((me.HEIGHT-me.oy) / me.sz, \
                           (me.WIDTH -me.ox) / me.sz) # rows-1, columns-1
        me.font = font if font else font8x8()
        
        if font and me.cursor.show == TRUE:
            me.put ('_')


    def page_flush (me, pages): raise NotImplementedError()


    def _put_ (me, char):
        '''
        page(s) of the row
        mask(s) of the row
        the row will cover one page or several pages
        '''
        rem = ((me.cursor.row+1) * me.sz + me.oy) % me.PAGE
        pages = range(((me.cursor.row)   * me.sz + me.oy) / me.PAGE, \
                      ((me.cursor.row+1) * me.sz + me.oy) / me.PAGE + (1 if rem>0 else 0))
        masks = [0xff] * len(pages)
        masks[0] = 0xff << rem
        if rem > 0:
            masks[-1] = 0xff >> (me.PAGE-rem)

        for yy in me.pages_row():
            for xx in range(me.PAGE):
                me.buffer[me.WIDTH *me.cursor.row + \
                          me.PAGE  *me.cursor.col + xx] = \
                          me.font.bitmap[ord(char)-ord(' ')][xx]


    def put (me, char):
        for xx in range(me.PAGE):
            me.buffer[me.WIDTH *me.cursor.row + \
                      me.PAGE  *me.cursor.col + xx] = \
                      me.font.bitmap[ord(char)-ord(' ')][xx]


    def scroll (me, row):
        '''
        returns all the pages for flushing
        '''
        for xx in range(me.cursor.height):
            for yy in range(me.WIDTH):
                me.buffer[me.WIDTH * xx      + yy] = \
                me.buffer[me.WIDTH *(xx+row) + yy] if xx+row < me.cursor.height else 0

        return range(me.cursor.height)


    def putc (me, char, wrap=FALSE, flush=TRUE):
        '''
        support wrap option
        '''
        pages = [me.cursor.row] # page needs flushing
        (scroll, line_feed, erase) = (FALSE, FALSE, me.cursor.show)
        if wrap == TRUE and me.cursor.col >= me.cursor.width:
            erase = FALSE
            (scroll, line_feed) = me.cursor.move_right (wrap)

        if me.cursor.col < me.cursor.width:
            if ord(char)>=ord(' ') and ord(char)<127: # printable
                me.put (char)
                (scroll, line_feed) = me.cursor.move_right (wrap)
            elif erase == TRUE:
                me.put (' ') # erase the cursor

        if   ord(char) == 0x08: # BS
            me.cursor.move_left ()
            me.put (' ') # erase the character
        elif ord(char) == 0x0A: # LF (^j/J)
#           print 'LF'
            (scroll, line_feed) = (me.cursor.line_feed (), me.cursor.show)
        elif ord(char) == 0x0C: # FF (^l/L)
#           print 'FF'
            pages = me.scroll (me.cursor.height)
            (scroll, line_feed) = (FALSE, FALSE)
            me.cursor.reset ()
        elif ord(char) == 0x0D: # CR
#           print 'CR'
            me.cursor.col = 0
            if wrap == TRUE:
                (scroll, line_feed) = (me.cursor.line_feed (), me.cursor.show)

        if   scroll    == TRUE: pages = me.scroll (1)
        elif line_feed == TRUE and \
             me.cursor.show == TRUE: pages += [me.cursor.row]

        if me.cursor.show == TRUE: me.put ('_')
        if flush == TRUE: me.page_flush (pages)


    def puts (me, text, align='left'):
        '''
        no wrap
        '''
        if   align=='left'  : me.cursor.col = 0
        elif align=='right' : me.cursor.col = me.cursor.width - len(text)
        elif align=='center': me.cursor.col = (me.cursor.width - len(text))/2
        else: print 'align error'
        for yy in text:
            me.putc (yy, TRUE, TRUE)

#       me.page_flush ([me.cursor.row])



class sh1106 (text_frame):

    _SET_CONTRAST        = 0x81
    _SET_NORM_INV        = 0xa6
    _SET_DISP            = 0xae
    _SET_SCAN_DIR        = 0xc0
    _SET_SEG_REMAP       = 0xa0
    _LOW_COLUMN_ADDRESS  = 0x00
    _HIGH_COLUMN_ADDRESS = 0x10
    _SET_PAGE_ADDRESS    = 0xb0

    def __init__ (me, i2cmst=None, font=None, flush=TRUE, on=TRUE, off=TRUE):
        text_frame.__init__ (me, font)
        me.busmst = i2cmst
        me.off = off
        if flush: me.page_flush (range(me.HEIGHT/me.PAGE)) # clear all
        if on: me.poweron ()

    def __del__ (me):
        if me.off: me.poweroff ()
#       print 'class %s died' % (me.__class__.__name__)

    def write_cmd (me, cmd):
        me.busmst.write (0x3c,0x80,[cmd]) # Co=1, D/C#=0

    def write_dat (me, buf):
        me.busmst.write (0x3c,0x40,buf)

    def poweron (me):
        me.write_cmd (me._SET_DISP | 0x01)

    def poweroff (me):
        me.write_cmd (me._SET_DISP | 0x00)

    def page_flush (me, pages):
        for page in pages:
            me.write_cmd (me._SET_PAGE_ADDRESS | page)
            me.write_cmd (me._LOW_COLUMN_ADDRESS | 2)
            me.write_cmd (me._HIGH_COLUMN_ADDRESS | 0)
            me.write_dat (me.buffer[me.WIDTH*page : me.WIDTH*(page+1)])



if __name__ == '__main__':

    def test_loop (item):
        import msvcrt,random,time
        while 1:
            for xx in range(display.cursor.height):
                for yy in range(len(display.buffer)):
                    if   item=='blink': display.buffer[yy] = 0x80 >> random.randint(0,800) # xx
                    elif item=='hline': display.buffer[yy] = 0x80 >> xx
                    elif item=='vline': display.buffer[yy] = 0xff if yy%8==xx else 0
                display.page_flush (range(display.cursor.height)) # flush all
#               if item!='blink': time.sleep (0.3)
                if msvcrt.kbhit(): break
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if   char == '0': item = 'blink'
                elif char == '1': item = 'vline'
                elif char == '2': item = 'hline'
                else: break

    def test_fonts (fontFilePath):
        import sys, glob
        flist = glob.glob(fontFilePath+'/*.?tf')
        if len(flist)==0: flist = glob.glob(fontFilePath+'*.?tf')
        if len(flist)==0: flist = [fontFilePath]
        for ffile in flist:
            print ffile.split('\\')[-1]
            display.font = font8x8(ffile,8)
            for yy in range(len(display.font.bitmap)):
                for zz in range(8):
                    display.buffer[yy*8 + zz] = display.font.bitmap[yy][zz]
            display.page_flush (range(display.HEIGHT/display.PAGE))
            if msvcrt.getch() == 'q':
                break

    def test_text (text=''):
        import msvcrt
#       display.font = font8x8('.\\font\\ModernDOS.ttf',8)
#       font_path = '/'.join(__file__.replace('\\','/').split('/')[0:-1]) + '/ModernDOS.ttf'
#       display.font = font8x8(font_path,8)
        display.font = font8x8()
        if text != '':
            display.puts ('Canyon-Semi\x0d')
            display.puts (__file__.replace('\\','/').split('/')[-1] + '\x0d')
            display.puts (text, 'right')
        char = 0
        while char != chr(27):
            char = msvcrt.getch()
            display.putc (char, TRUE)

    def test_only ():
        pass

    from cynpy.basic import *
    if not no_argument ():

#       for pp in sys.path: print pp

        import i2c
        i2cmst = i2c.choose_master ()
#       assert i2cmst.probe ()[0]==0x3C, 'SH1106 device not found'

        display = sh1106(i2cmst)

        if   sys.argv[1]=='loop' : test_loop (sys.argv[2])
        elif sys.argv[1]=='font' : test_fonts (sys.argv[2])
        elif sys.argv[1]=='text' : test_text (sys.argv[2])
        elif sys.argv[1]=='type' : test_text ()
        elif sys.argv[1]=='test' : test_only ()
        else: print "command not recognized"

