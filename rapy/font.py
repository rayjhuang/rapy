
import string
from PIL import Image, ImageFont

class mpyfont:
    '''
    '''
    def __init__ (me, fontFilePathName='', sz=-1):
        me.target = ''
        for char in sorted(string.printable):
            if char>=' ' and char<='~':
                me.target += char

        if fontFilePathName=='':
            fontFilePathName = '/'.join(__file__.replace('\\','/').split('/')[0:-1]) + '/ModernDOS.ttf'

        me.ttfont = ImageFont.truetype (fontFilePathName) if sz<0 \
               else ImageFont.truetype (fontFilePathName, sz)

        me.bitmap = [[]] * len(me.target)
        (me.sz_x, me.sz_box) = me.ttfont.getsize(me.target)

        me.loadBitMap ()

    def loadBitMap (me):
        for idx in range(len(me.target)):
            (ofx,ofy) = me.ttfont.getoffset(me.target[idx])
            if ofy<0: ofy = 0 # not support negtive offset
            if ofx<0: ofx = 0 # not support negtive offset
            me.bitmap[idx] = [0] * me.sz_box # initial a HxH array (support H<=32??)
            im = Image.Image()._new(me.ttfont.getmask(me.target[idx],'1')) # bitmap
            delCount = 0
            for xx in range(im.width):
                if xx+ofx < me.sz_box:
                    bit = '0' * ofy
                    for yy in range(im.height):
                        bit = ('1' if im.getpixel((xx,yy)) else '0') + bit
                    me.bitmap[idx][xx+ofx] = int('0'+bit,2)
                else:
                    delCount += 1
                    break
            if delCount:
                print '%c, w: %d, h:%d' % (me.target[idx],im.width,im.height),
                print me.ttfont.getoffset(me.target[idx])

    def showBitmap (me, chars=''):
        if chars == '':
            me.showChar (-1)
##            for idx in range(len(me.bitmap)):
##                print '[',
##                for xx in range(len(me.bitmap[idx])):
##                    print '%03x' % (me.bitmap[idx][xx]),
##                print '] #',
##                print '%c : %d' % (me.target[idx],idx) \
##                      if idx<len(me.target) \
##                      else 'dummy'
        else:
            for cc in chars:
                for zz in range(len(me.target)):
                    if me.target[zz] == cc:
                        me.showChar (zz)

    def showChar (me, idx):
        text = me.target if idx < 0 else me.target[idx]
        (szx,szy) = me.ttfont.getsize(text)
        print 'offset    ', me.ttfont.getoffset(text)
        print 'char size ', (szx,szy)

        im = Image.Image()._new(me.ttfont.getmask(text,'1'))
        print 'image size', (im.width,im.height)
        for xx in range(im.width):
            bits = ''
            for yy in range(im.height):
                bits = ('#' if im.getpixel((xx,yy)) else '-') + bits
            print bits


class font8x8 (mpyfont):
    def __init__ (me, fontFilePathName='', sz=8):
        mpyfont.__init__ (me, fontFilePathName, sz)
#       assert me.sz_box == 8, 'not a compatible font, %d' % (me.sz_box)

    def loadBitMap (me):
        for idx in range(len(me.target)):
            (ofx,ofy) = me.ttfont.getoffset(me.target[idx])
            if ofx<0: ofx = 0 # not support negtive offset
            if ofy<0: ofy = 0 # not support negtive offset
            me.bitmap[idx] = ([0]*8) # initial a 8x8 array
            im = Image.Image()._new(me.ttfont.getmask(me.target[idx],'1'))
            for xx in range(min(8-ofx,im.width)):
                bit = '0' * ofy
                for yy in range(min(8-ofy,im.height)):
                    bit = ('1' if im.getpixel((xx,yy)) else '0') + bit
                me.bitmap[idx][xx+ofx] = int('0'+bit,2)
                assert me.bitmap[idx][xx+ofx]<256, 'bitmap error, %s,%d,%c' % (bit,xx,me.target[idx])


if __name__ == '__main__':

    import glob, os
    def test_brief (fontFilePath, sz):
        for ffile in [fontFilePath] + glob.glob(fontFilePath+'/*.?tf'):
            if os.path.isfile (ffile):
                ttfont = mpyfont(ffile, sz)
                print '(%3d,%3d) %s' % (ttfont.sz_x, ttfont.sz_box, ffile.split('\\')[-1])

    def test_chars (fontFilePathName, sz, chars=''):
        font = mpyfont(fontFilePathName, sz)
        print '(%d,%d) %s' % (font.sz_x, font.sz_box, fontFilePathName)
        font.showBitmap (chars)

    def test_only (fontFilePath, sz):
        target = ''
        for char in sorted(string.printable):
            if char>=' ' and char<='~':
                target += char

        files = glob.glob (fontFilePath+'/Mo*.?tf')
#       target = 'ABC_xyz'

        from PIL import Image, ImageFont
        print 'PILLOW_VERSION', Image.PILLOW_VERSION
        for xx in range(len(files)):
            font = ImageFont.truetype (files[xx], sz)
            max_width = 0
            for yy in range(len(target)):
                bitmap = font.getmask(target[yy])
                if bitmap.size[0] > max_width:
                    max_width = bitmap.size[0]

            bitmap = font.getmask(target)
            avg_width = bitmap.size[0]/len(target)
            max_pt_line = 128
            char_per_line = max_pt_line/avg_width
            num_line = bitmap.size[0]/(char_per_line*avg_width) + \
                                  (1 if bitmap.size[0]%max_pt_line>0 else 0)
            print char_per_line, num_line
            print '%2d..%2d max:%2d (%4dx%2d) %s' % (avg_width, \
                        bitmap.size[0]%len(target), max_width, \
                        bitmap.size[0], bitmap.size[1], files[xx])
            for zz in range(num_line):
                for yy in range(bitmap.size[1]): # height
                    bits = ''
                    for kk in range(char_per_line*avg_width):
                        if zz*char_per_line*avg_width+kk < bitmap.size[0]:
                            bits += 'X' if bitmap.getpixel((zz*char_per_line*avg_width+kk,yy)) > 0 else '-'
                    print bits
                print



        

    from cynpy.basic import *
    if not no_argument ():
        if   sys.argv[1]=='brief' : test_brief (sys.argv[2],argv_dec[3])
        elif sys.argv[1]=='chart' : test_chars (sys.argv[2],argv_dec[3])
        elif sys.argv[1]=='char'  : test_chars (sys.argv[2],argv_dec[3],sys.argv[4])
        elif sys.argv[1]=='test'  : test_only  (sys.argv[2],argv_dec[3])
        else: print "command not recognized"


