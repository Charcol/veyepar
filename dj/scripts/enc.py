#!/usr/bin/python

# encodes to ogg

import os,sys,subprocess
import xml.etree.ElementTree

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

BPF=120000
FPS=29.98

mlt="""
<mlt>

  <producer id="title" 
    resource="title.png" in="0" out="149" />
  <producer id="producer0" resource="/home/juser/vid/t2.dv" />

  <playlist id="playlist0">
    <entry id="clip" producer="producer2" in="500" out="690" />
    <filter mlt_service="channelcopy" from="1" to="0" />
    <filter mlt_service="volume" max_gain="30" normalise="28" />
  </playlist>

  <playlist id="playlist1">
    <entry producer="title"/>
  </playlist>

  <tractor id="tractor0">
       <multitrack>
         <track producer="playlist0"/>
         <track producer="playlist1"/>
       </multitrack>
       <transition 
         mlt_service="luma" in="100" out="149" a_track="1" b_track="0"/>
   </tractor>

</mlt>
"""

def run_cmd(cmd):
    print cmd
    cmd = cmd.split()
    print cmd
    p=subprocess.Popen(cmd)
    p.wait()
    retcode=p.returncode
    return retcode


def mktitle(name, authors):
    svg_in=open('/home/carl/dev/py/vid/djcon/djc09b.svg').read()
    tree=xml.etree.ElementTree.XMLID(svg_in)
    # print tree[1]
    tree[1]['title'].text=name
    tree[1]['presenternames'].text="By %s" % authors
    open('x.svg','w').write(xml.etree.ElementTree.tostring(tree[0]))
    cmd="inkscape x.svg --export-png title.png"
    run_cmd(cmd)

def time2s(time):
    """ given 's.s' or 'h:m:s.s' returns s.s """
    if ':' in time:
        sec = reduce(lambda x, i: x*60 + i, 
            map(float, time.split(':')))  
    else:
        print time, len(time), [c for c in time]
        sec = float(time)
    return sec

def time2f(time,fps):
    if time[-1]=='f':
        return int(time[:-1])
    else:
        return time2s(time)*fps

def time2b(time,fps,bpf,default):
    """
    converts the time stored in the db 
      (as blank, seconds,  h:m:s.s )
    to the byte offset in the file.
    blank returns default, typically either 0 or filesize for start/end.
    fps is 25.0 for pal and 29.9 ntsc.
    bpf (bytes per frame) is 120000 for both.
    """
    if time:
        bytes = int(time2s(time)*fps)*bpf
    else:
        bytes = default
    return bytes

class enc(process):

  ready_state = 2
  done_state = 3


  def process_ep(self,episode):
    print 1, episode
    ret = False
    cls = Cut_List.objects.filter(episode=episode).order_by('sequence')
    if cls:
        rfs = Raw_File.objects.filter(cut_list__episode=episode).distinct()

        tree= xml.etree.ElementTree.XMLID(mlt)

# get the dvfile placeholder and remove it from the tree
        dvfile=tree[1]['producer0']
        tree[0].remove(dvfile)

# add in the dv files
        pos = 1
        for rf in rfs:
            print rf
            dvfile.attrib['id']="producer%s"%rf.id
            rawpathname = os.path.join(self.episode_dir,rf.filename)
            dvfile.attrib['resource']=rawpathname
            # new=xml.etree.ElementTree.SubElement(tree[0],'producer', dvfile.attrib )
            new=xml.etree.ElementTree.Element('producer', dvfile.attrib )
            tree[0].insert(pos,new)
            pos+=1

        xml.etree.ElementTree.dump(tree[0])
        print tree[1]

# get the clip placeholder, the playlist and remove the clip from the playlist
        clip=tree[1]['clip']
        playlist=tree[1]['playlist0']
        playlist.remove(clip)

# add in the clips
        pos = 0
        # for id,start,end in [(1,'500','690'),(2,'1000',None)]:
        for cl in cls:
            print cl
            clip.attrib['id']="clip%s"%cl.id
            clip.attrib['producer']="producer%s"%cl.raw_file.id
            clip.attrib['in']=str(time2f(cl.start,FPS)) if cl.start else '0'
            clip.attrib['out']=str(time2f(cl.end,FPS)) if cl.end else '999999'
            new=xml.etree.ElementTree.Element('entry', clip.attrib )
            playlist.insert(pos,new)
            pos+=1

        xml.etree.ElementTree.dump(tree[0])

        open('x.mlt','w').write(xml.etree.ElementTree.tostring(tree[0]))

        mktitle(episode.name, episode.authors)

        oggpathname = os.path.join(self.show_dir, "ogg", "%s.ogg"%episode.slug)
        cmd="melt -verbose -profile dv_ntsc x.mlt -consumer avformat:%s acodec=vorbis ab=128k ar=44100 vcodec=libtheora minrate=0 b=600k" % oggpathname
        ret = run_cmd(cmd)

    else:
        print "No cutlist found."

    return False


  def old_proc_ep(self):
    if cl:
        oggpathname = os.path.join(self.show_dir, "ogg", "%s.ogg"%episode.slug)
        cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd+=['--output',oggpathname]
        if len(cl)==1:
            # use the raw dv file and ffmpeg2theora params to trim
            c=cl[0]
            if c.start: cmd+=['--starttime',str(time2s(c.start))]
            if c.end: cmd+=['--endtime',str(time2s(c.end))]
            dvpathname = os.path.join(self.episode_dir,c.raw_file.filename)
        else:
            # make a new dv file using just the frames to encode
            dvpathname = os.path.join(self.episode_dir,episode.slug+".dv")
            outf=open(dvpathname,'wb')
            for c in cl:
                print (c.raw_file.filename, c.start,c.end)
                rawpathname = os.path.join(self.episode_dir,c.raw_file.filename)
                inf=open(rawpathname,'rb')
                inf.seek(time2b(c.start,29.9,BPF,0))
                size=os.fstat(inf.fileno()).st_size
                end = time2b(c.end,29.9,BPF,size)
                while inf.tell()<end:
                    outf.write(inf.read(BPF))
                inf.close()
            outf.close()
        
        cmd+=[dvpathname]
        print ' '.join(cmd)
        p=subprocess.Popen(cmd)
        p.wait()
        retcode=p.returncode
        if not retcode and os.path.exists(oggpathname):
            ret = True
        else:
            print episode.id, episode.name
            print "transcode failed"
            print retcode, os.path.exists(oggpathname)
    else:
        print "No cutlist found."

    return ret

if __name__ == '__main__':
    p=enc()
    p.main()

