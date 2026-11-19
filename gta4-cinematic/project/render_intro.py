"""Render the 90 BPM GTA IV-inspired fan intro from the editable photo layers.

The default score was synthesized specifically for this cut; it is not the
GTA IV soundtrack. If a music file is supplied, it replaces the custom score;
adjust the edit to the new track manually because beat detection is not used.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
import imageio_ffmpeg
from intro_design import BASE, W, H, FPS, BEAT_FRAMES, SCENES, build_scene

FF = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
TRANSITION_FRAMES = 8
GROUP_SIZE = 5


def run(args):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if result.returncode:
        raise RuntimeError("FFmpeg failed:\n"+result.stderr[-8000:])
    return result


def validate(enforce_beat=True):
    if enforce_beat and any(s.frames%BEAT_FRAMES for s in SCENES):
        raise ValueError("All scene starts must remain on the 90 BPM beat grid for the custom score")
    for s in SCENES:
        required=[BASE/'assets'/'plates'/f'{s.plate}.jpg']
        if s.photo:
            required += [BASE/'processed'/f'{s.photo}_gta4.jpg',
                         BASE/'assets'/'cinematic_16x9'/f'{s.photo}_16x9.jpg',
                         BASE/'assets'/'intro_masks'/f'{s.photo}.png']
        for p in required:
            if not p.is_file():raise FileNotFoundError(p)
    for f in ['Anton-Regular.ttf','IBMPlexMono-Medium.ttf']:
        p=BASE/'assets'/'fonts'/f
        if not p.is_file():raise FileNotFoundError(p)


def render_scene(scene,index,output,art,extra):
    background,foreground,title=build_scene(scene,index,art)
    frames=scene.frames+extra
    seconds=frames/FPS
    cmd=[FF,'-hide_banner','-loglevel','error','-y','-filter_complex_threads','1',
         '-loop','1','-framerate',str(FPS),'-i',str(background)]
    if foreground:
        cmd+=['-loop','1','-framerate',str(FPS),'-i',str(foreground)]
    cmd+=['-loop','1','-framerate',str(FPS),'-i',str(title)]

    # The city/photo panel drifts subtly; the foreground enters independently.
    # d=1 ensures a looped image produces exactly one output frame per frame.
    progress=f'on/{max(1,frames-1)}'
    z=f'1.018+0.025*({progress})' if index%2==0 else f'1.043-0.025*({progress})'
    x="(iw-iw/zoom)*.42" if scene.side=='right' else "(iw-iw/zoom)*.58"
    bg=(f'[0:v]scale={W}:{H},zoompan=z=\'{z}\':x=\'{x}\':'
        f'y=\'(ih-ih/zoom)/2\':d=1:s={W}x{H}:fps={FPS},setsar=1[bg]')
    graph=[bg]
    if foreground:
        sign=1 if scene.side=='right' else -1
        xpos=f'if(lt(t,0.50),{sign}*100*(1-t/0.50)*(1-t/0.50),0)+{sign}*12*t/{seconds:.5f}'
        graph += ['[1:v]format=rgba,fade=t=in:st=0:d=0.20:alpha=1[figure]',
                  f"[bg][figure]overlay=x='{xpos}':y=0:shortest=1:format=auto[composite]"]
        title_input=2
    else:
        graph += ['[bg]null[composite]'];title_input=1
    graph += [f'[{title_input}:v]format=rgba,fade=t=in:st=0.12:d=0.42:alpha=1[type]',
              "[composite][type]overlay=x='if(lt(t,0.50),-14*(1-t/0.50),0)':y=0:shortest=1:format=auto[framed]"]
    fades=''
    if scene.key=='opening':fades+=',fade=t=in:st=0:d=0.5'
    if scene.key=='closing':fades+=f',fade=t=out:st={scene.frames/FPS-1.25:.4f}:d=1.25'
    graph += [f'[framed]null{fades},scale=iw:ih:in_range=full:out_range=tv,format=yuv420p,'
              'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[out]']
    cmd += ['-filter_complex',';'.join(graph),'-map','[out]','-frames:v',str(frames),'-an',
            '-c:v','libx264','-preset','veryfast','-crf','17','-threads','2','-pix_fmt','yuv420p',
            '-r',str(FPS),'-color_range','tv','-color_primaries','bt709','-color_trc','bt709',
            '-colorspace','bt709',str(output)]
    run(cmd)


def render_group(shots,clips,output,group_index):
    cmd=[FF,'-hide_banner','-loglevel','error','-y','-filter_complex_threads','1']
    for clip in clips:cmd+=['-i',str(clip)]
    filters=[f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]' for i in range(len(clips))]
    prev='v0';elapsed=shots[0].frames
    for i in range(1,len(shots)):
        # Each previous clip is extended by TRANSITION_FRAMES. The transition
        # starts on the next scene's musical beat, without shortening the edit.
        off=elapsed/FPS
        transition=shots[i].split
        filters.append(f'[{prev}][v{i}]xfade=transition={transition}:'
                       f'duration={TRANSITION_FRAMES/FPS:.6f}:offset={off:.6f}[vout{i}]')
        prev=f'vout{i}';elapsed+=shots[i].frames
    filters.append(f'[{prev}]format=yuv420p[out]')
    cmd+=['-filter_complex',';'.join(filters),'-map','[out]','-frames:v',str(elapsed),'-an',
          '-c:v','libx264','-preset','medium','-crf','19','-threads','2','-pix_fmt','yuv420p','-r',str(FPS),
          '-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(output)]
    print(f'Combining section {group_index+1} ({elapsed/FPS:.2f}s)',flush=True)
    run(cmd)
    return elapsed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--music',type=Path,help='replace the custom score with a supplied track (manual beat sync needed)')
    p.add_argument('--music-offset',type=float,default=0,help='seconds to skip in supplied track')
    p.add_argument('--test-scenes',type=int,default=0,help='render only the first N scenes to .qc/ for testing')
    args=p.parse_args()
    if not 0<=args.test_scenes<=len(SCENES):p.error('--test-scenes out of range')
    if args.music and not args.music.is_file():p.error(f'No such audio file: {args.music}')
    if args.music_offset<0:p.error('--music-offset cannot be negative')
    validate(enforce_beat=not bool(args.music))
    audio=args.music or BASE/'audio'/'original_score_90bpm.m4a'
    if not audio.is_file():raise FileNotFoundError(f'{audio}; run compose_score.py first')
    shots=SCENES[:args.test_scenes] if args.test_scenes else SCENES
    root=BASE.parent/'.cache';root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='liberty-intro-',dir=root) as tmp:
        tmp=Path(tmp);clips=[]
        for i,scene in enumerate(shots):
            clip=tmp/f'shot_{i:02d}.mp4'
            extra=0 if (i%GROUP_SIZE==GROUP_SIZE-1 or i==len(shots)-1) else TRANSITION_FRAMES
            print(f'Rendering {i+1:02}/{len(shots)} {scene.key} ({scene.frames/FPS:.2f}s)',flush=True)
            render_scene(scene,i,clip,tmp/'art',extra)
            clips.append(clip)
        groups=[];total_frames=0
        for k in range(0,len(shots),GROUP_SIZE):
            group=tmp/f'group_{k//GROUP_SIZE:02d}.mp4'
            total_frames+=render_group(shots[k:k+GROUP_SIZE],clips[k:k+GROUP_SIZE],group,k//GROUP_SIZE)
            groups.append(group)
        listing=tmp/'list.txt'
        listing.write_text(''.join(f"file '{g.as_posix()}'\n" for g in groups),encoding='utf-8')
        silent=tmp/'silent.mp4'
        run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),
             '-map','0:v:0','-c','copy',str(silent)])
        duration=total_frames/FPS
        if args.test_scenes:
            dest=BASE.parent/'.qc'/'intro_test.mp4';dest.parent.mkdir(exist_ok=True)
        elif args.music:
            dest=BASE/'output'/'gta4_liberty_city_with_user_music.mp4'
        else:
            dest=BASE/'output'/'gta4_liberty_city_intro.mp4'
        dest.parent.mkdir(exist_ok=True)
        if args.music:
            # This is only a replacement, not an automatic synchronization.
            audio_filter=(f'atrim=start={args.music_offset:.3f},asetpts=PTS-STARTPTS,apad,'
                          f'atrim=duration={duration:.6f},afade=t=in:st=0:d=1,'
                          f'afade=t=out:st={max(0,duration-2):.3f}:d=2,aresample=48000')
            run([FF,'-hide_banner','-loglevel','error','-y','-i',str(silent),'-i',str(audio),
                 '-map','0:v:0','-map','1:a:0','-filter:a',audio_filter,'-c:v','copy',
                 '-c:a','aac','-b:a','192k','-ac','2','-t',f'{duration:.6f}','-movflags','+faststart',str(dest)])
        else:
            run([FF,'-hide_banner','-loglevel','error','-y','-i',str(silent),'-i',str(audio),
                 '-map','0:v:0','-map','1:a:0','-c','copy','-t',f'{duration:.6f}',
                 '-movflags','+faststart',str(dest)])
        print(f'Saved {dest} — {duration:.3f}s, {W}x{H}, {FPS}fps',flush=True)
        if args.music:print('Supplied music replacement: adjust cuts manually for its beat.',flush=True)
        else:print('Original custom score, 90 BPM; not the GTA IV soundtrack.',flush=True)


if __name__=='__main__':main()
