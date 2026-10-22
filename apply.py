#!/usr/bin/env python3
"""Builds the modded OP-1 firmware from the official one. Python 3.8 or newer, nothing to install.

    python3 apply.py op1_246.op1 op1-mod.op1patch

Reads the official firmware file you downloaded from Teenage Engineering, checks it is the exact file the patch was
made for, and writes the modded firmware next to it. The patch contains only the changes, never the firmware."""
import sys,lzma,zlib,hashlib,json,struct,os
def main():
    if len(sys.argv)<3: sys.exit(__doc__)
    basep,patchp=sys.argv[1],sys.argv[2]
    p=open(patchp,'rb').read()
    if p[:8]!=b'OP1PATCH': sys.exit('That is not a patch file: '+patchp)
    n=struct.unpack_from('<I',p,8)[0]; head=json.loads(p[12:12+n]); body=zlib.decompress(p[12+n:])
    d=open(basep,'rb').read()
    if hashlib.sha256(d).hexdigest()!=head['base_sha256']:
        sys.exit('This is not the firmware file the patch was made for.\n  expected SHA-256 %s\n  got               %s\nNothing was written.'%(head['base_sha256'],hashlib.sha256(d).hexdigest()))
    if struct.unpack('<I',d[:4])[0]!=zlib.crc32(d[4:]): sys.exit('The firmware file is damaged (CRC). Nothing was written.')
    base=lzma.decompress(d[4:],format=lzma.FORMAT_ALONE)
    out=bytearray(); o=0
    while o<len(body):
        if body[o:o+1]==b'C': a,l=struct.unpack_from('<II',body,o+1); out+=base[a:a+l]; o+=9
        else: l=struct.unpack_from('<I',body,o+1)[0]; out+=body[o+5:o+5+l]; o+=5+l
    if len(out)!=head['tar_size'] or hashlib.sha256(out).hexdigest()!=head['tar_sha256']: sys.exit('The result does not match the patch. Nothing was written.')
    comp=lzma.compress(bytes(out),format=lzma.FORMAT_ALONE,preset=6)
    name=sys.argv[3] if len(sys.argv)>3 else os.path.join(os.path.dirname(os.path.abspath(basep)),'op1_246_%s_%s.op1'%(head['name'],head['version']))
    open(name,'wb').write(struct.pack('<I',zlib.crc32(comp)&0xffffffff)+comp)
    back=open(name,'rb').read()                       # read it back the way the OP-1's loader will
    assert struct.unpack('<I',back[:4])[0]==zlib.crc32(back[4:]) and lzma.decompress(back[4:],format=lzma.FORMAT_ALONE)==bytes(out)
    print('Wrote',name,'(%s %s). Verified.'%(head['name'],head['version']))
if __name__=='__main__': main()
