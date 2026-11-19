"""Technical checks and a scene contact sheet for the Liberty City intro."""
from pathlib import Path
import hashlib
import io
import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageOps, ImageStat
from intro_design import BASE, W, H, FPS, BEAT_FRAMES, SCENES
from render_intro import FF


def ff(*args, check=True):
    return subprocess.run([FF,*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)


def main():
    video=Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'output'/'gta4_liberty_city_intro.mp4'
    if not video.is_file():raise FileNotFoundError(video)
    originals=sorted((BASE/'originals').glob('*.jpeg'))
    if len(originals)!=16:raise ValueError(f'Expected 16 originals, found {len(originals)}')
    selected={s.photo for s in SCENES if s.photo}
    missing=[p.name for p in originals if p.stem not in selected]
    if missing:raise ValueError(f'Photo(s) absent from edit: {missing}')
    for p in originals:
        out=BASE/'processed'/f'{p.stem}_gta4.jpg'
        if not out.exists():raise FileNotFoundError(out)
        with Image.open(p) as src,Image.open(out) as graded:
            if ImageOps.exif_transpose(src).size!=graded.size:
                raise ValueError(f'Processed photo resolution differs: {p.name}')
    upload=Path('/tmp/arena-coding-uploads')
    if upload.is_dir() and all((upload/p.name).is_file() for p in originals):
        for p in originals:
            if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256((upload/p.name).read_bytes()).digest():
                raise ValueError(f'Original does not match upload: {p.name}')
        print('Original SHA-256 hashes match all 16 uploads.')
    if any(s.frames%BEAT_FRAMES for s in SCENES):raise ValueError('Scene timings are not on the custom score beat grid')
    expected=sum(s.frames for s in SCENES)/FPS
    text=ff('-hide_banner','-i',str(video),check=False).stderr.decode('utf8','replace')
    vl=next((x.strip() for x in text.splitlines() if 'Video:' in x),'')
    al=next((x.strip() for x in text.splitlines() if 'Audio:' in x),'')
    match=re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)',text)
    if not match:raise ValueError('Duration unavailable')
    duration=int(match[1])*3600+int(match[2])*60+float(match[3])
    if abs(duration-expected)>1/FPS+.01:raise ValueError(f'Duration {duration}, expected {expected}')
    if f'{W}x{H}' not in vl or f'{FPS} fps' not in vl or 'h264' not in vl.lower():raise ValueError(vl)
    if 'aac' not in al.lower():raise ValueError(f'Audio missing: {al}')
    print(f'{len(originals)} originals and full-resolution processed images; all included in edit.')
    print(f'Duration {duration:.2f}s; {vl}; {al}')
    print('Decoding complete video and audio...',flush=True)
    ff('-v','error','-i',str(video),'-f','null','-')
    volume=ff('-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-').stderr.decode('utf8','replace')
    for line in volume.splitlines():
        if 'mean_volume' in line or 'max_volume' in line:print(line.strip())
    width,height,label,columns=480,270,24,4
    rows=(len(SCENES)+columns-1)//columns
    sheet=Image.new('RGB',(width*columns,(height+label)*rows),(8,11,12));draw=ImageDraw.Draw(sheet)
    frame=0
    for i,s in enumerate(SCENES):
        t=(frame+s.frames/2)/FPS
        image_bytes=ff('-v','error','-ss',f'{t:.4f}','-i',str(video),'-frames:v','1',
                       '-f','image2pipe','-vcodec','mjpeg','-q:v','2','-').stdout
        image=Image.open(io.BytesIO(image_bytes)).convert('RGB').resize((width,height),Image.Resampling.LANCZOS)
        if max(ImageStat.Stat(image).mean)<2:raise ValueError(f'Unexpected black midpoint: {s.key}')
        x=(i%columns)*width;y=(i//columns)*(height+label);sheet.paste(image,(x,y))
        draw.text((x+5,y+height+4),f'{i+1:02} | {t:05.1f}s | {s.key}',fill='white')
        frame+=s.frames
    out=BASE.parent/'.qc'/'intro_contact_sheet.jpg';out.parent.mkdir(exist_ok=True);sheet.save(out,quality=90)
    print(f'Decode and scene samples passed. Contact sheet: {out}')
    print('The track is an original synthetic 90 BPM score, not the GTA IV soundtrack.')
    print('Manual review and any synchronization to a user-supplied track remain separate tasks.')


if __name__=='__main__':main()
