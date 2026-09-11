"""Silent, real-time isolated display recording for the private trailer."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time


class Recording:
    def __init__(self, out, audio=False):
        self.out=Path(out); self.process=None; self.module=None; self.log=None
        self.sink=f'af_trailer_{os.getpid()}'; self.markers=[]; self.started=None
        self.audio=audio

    def configure(self, env):
        # A private null sink clocks the muted emulator, without a route to
        # physical outputs. Never change the user's default sink or links.
        self.module=subprocess.check_output(['pactl','load-module','module-null-sink',
            f'sink_name={self.sink}',f'sink_properties=device.description={self.sink}',
            'rate=48000'],text=True,timeout=10).strip()
        if not self.module.isdigit(): raise ValueError('Unexpected null-sink module ID')
        sinks=json.loads(subprocess.check_output(['pactl','--format=json','list','sinks'],text=True,timeout=10))
        if not any(s['name']==self.sink for s in sinks): raise ValueError('Recording null sink missing')
        env.pop('PULSE_SERVER',None)
        if 'PULSE_SERVER' in os.environ: env['PULSE_SERVER']=os.environ['PULSE_SERVER']
        env['PULSE_SINK']=self.sink

    def start(self, display, env, duration):
        self.log=(self.out/'recording.log').open('wb')
        command=['ffmpeg','-nostdin','-hide_banner','-loglevel','warning',
            '-f','x11grab','-draw_mouse','0','-framerate','30','-video_size','800x640',
            '-i',display]
        if self.audio:
            # The explicit monitor belongs only to our verified null sink.
            # Never capture the user's microphone or default output monitor.
            command+=['-f','pulse','-sample_rate','48000','-channels','2',
                      '-i',self.sink+'.monitor','-map','0:v','-map','1:a',
                      '-c:a','pcm_s16le']
        else: command+=['-an']
        command+=['-t',str(duration),'-c:v','libx264','-preset','veryfast',
            '-crf','12','-pix_fmt','yuv420p',str(self.out/'footage.mkv')]
        self.process=subprocess.Popen(command,
            env=env,stdout=subprocess.DEVNULL,stderr=self.log)
        self.started=time.monotonic()
        self.mark('recording-start')

    def mark(self, label):
        if not isinstance(label,str) or len(label)>120: raise ValueError('Invalid recording marker')
        self.markers.append({'name':label,'seconds':round(time.monotonic()-self.started,3)})
        (self.out/'recording.json').write_text(json.dumps({'audio':
            'game audio captured from private null-sink monitor; no hardware playback' if self.audio
            else 'muted, private null sink',
            'sink':self.sink,'source_size':[800,640],'fps':30,'markers':self.markers},indent=2)+'\n')

    def stop(self):
        if self.process:
            if self.process.poll() is None: self.process.send_signal(signal.SIGINT)
            status=self.process.wait(timeout=15)
            self.process=None
            if status not in (0,255): raise ValueError(f'Video encoder exited with {status}')

    def close(self):
        try:
            self.stop()
        finally:
            if self.log: self.log.close(); self.log=None
            if self.module:
                subprocess.run(['pactl','unload-module',self.module],check=True,timeout=10,
                               stdout=subprocess.DEVNULL)
                self.module=None
