"""Render corrected recorded-footage review. Original source remains unchanged."""
from pathlib import Path
import json, math, subprocess, hashlib
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'rebuttal_demo_video.mp4'
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
INK='#182723'; PAPER='#f2f1e9'; GREEN='#365e4b'
def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=open(ROOT/'render.log','a'))
def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)]))
def ts(sec):
    ms=round(sec*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
scenes=json.loads((ROOT/'scenes.json').read_text()); timeline=[]; offset=0; all_srt=[]
for i,s in enumerate(scenes):
    voice=ROOT/f'voice-{i}.mp3'; length=duration(voice)
    total=math.ceil((length+1.6)*30)/30
    s['duration']=total
    x,y,w,h=s['crop']; out_w=1640; out_h=round(h*out_w/w/2)*2
    panel_y=310+(460-out_h)//2
    bg=Image.new('RGB',(1920,1080),PAPER); d=ImageDraw.Draw(bg)
    def text(x,y,t,size=32,bold=False,fill=INK):
        d.text((x,y),t,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=fill)
    text(120,54,'REBUTTAL',30,True)
    text(1280,60,'SYNTHETIC DATA / RECORDED DEMO',24,True,GREEN)
    d.line((120,115,1800,115),fill='#b8beb3',width=2)
    text(120,147,s['label'],23,True,GREEN)
    text(120,190,s['title'],62,True)
    d.rectangle((120,panel_y-12,1800,panel_y+out_h+12),fill='white',outline='#c2c9be',width=2)
    text(140,792,s['point'],35,True)
    text(140,846,s['note'],26,False,GREEN)
    d.rectangle((0,919,1920,1080),fill=INK)
    bg_path=ROOT/f'background-{i}.png'; bg.save(bg_path)
    words=json.loads((ROOT/f'voice-{i}.json').read_text()); captions=[]
    spoken=s['speech'].split()
    assert len(spoken)==len(words), 'Speech timing/token mismatch'
    k=0
    while k<len(words):
        end_index=k+1
        while end_index<len(words) and end_index-k<7 and not spoken[end_index-1].endswith(('.', ';', '?', '!')):
            end_index+=1
        group=words[k:end_index]; start=0.4+group[0]['offset']/1e7
        end=0.4+(group[-1]['offset']+group[-1]['duration'])/1e7
        phrase=' '.join(spoken[k:end_index])
        captions.append(f'{len(captions)+1}\n{ts(start)} --> {ts(end)}\n{phrase}\n')
        all_srt.append(f'{len(all_srt)+1}\n{ts(offset+start)} --> {ts(offset+end)}\n{phrase}\n')
        k=end_index
    srt=ROOT/f'captions-{i}.srt'; srt.write_text('\n'.join(captions))
    segment=ROOT/f'segment-{i}.mp4'
    # Whole synthesized speech is retained; no word cuts. Captions render last.
    filt=(f'[1:v]crop={w}:{h}:{x}:{y},scale={out_w}:{out_h},fps=30,setsar=1,'
          f'tpad=stop_mode=clone:stop_duration={total},setpts=PTS-STARTPTS[v];'
          f'[0:v][v]overlay=140:{panel_y}:shortest=1,'
          f"subtitles='{srt}':force_style='FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,Outline=0,Shadow=0,Alignment=2,MarginV=18'[out];"
          f'[2:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.03,afade=t=out:st={max(0,length-.03)}:d=0.03,'
          f'adelay=400:all=1,apad,atrim=duration={total},aresample=48000[a]')
    run([FF,'-y','-v','error','-loop','1','-framerate','30','-i',str(bg_path),
         '-ss',str(s['source']),'-t','6','-i',str(SOURCE),'-i',str(voice),
         '-filter_complex',filt,'-map','[out]','-map','[a]','-t',str(total),
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','30',
         '-c:a','aac','-b:a','192k','-ar','48000','-ac','2',str(segment)])
    timeline.append({'scene':i+1,'start':offset,'end':offset+total,'source_start':s['source'],'source_duration':6,'hold_last_frame':total-6,'speech':s['speech']})
    offset+=total
    print(f'Rendered scene {i+1}: {total:.2f}s',flush=True)
(ROOT/'concat.txt').write_text(''.join(f"file '{ROOT/f'segment-{i}.mp4'}'\n" for i in range(len(scenes))))
run([FF,'-y','-v','error','-f','concat','-safe','0','-i',str(ROOT/'concat.txt'),'-c','copy','-movflags','+faststart',str(ROOT/'rebuttal-corrected-preview.mp4')])
(ROOT/'captions.srt').write_text('\n'.join(all_srt))
(ROOT/'timeline.json').write_text(json.dumps(timeline,indent=2))
(ROOT/'source.sha256').write_text(hashlib.sha256(SOURCE.read_bytes()).hexdigest()+'  '+str(SOURCE)+'\n')
print(f'Complete: {offset:.2f}s',flush=True)
