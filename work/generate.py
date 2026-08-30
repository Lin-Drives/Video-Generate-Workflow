import json, os, subprocess, sys, urllib.request
from pathlib import Path
root, build = map(Path, sys.argv[1:]); out=root/'outputs'; build.mkdir(parents=True, exist_ok=True)
sections=[
('开场：冲刺的几秒','机器人冲刺时，到底是谁在出力？答案不是单独一台电机，而是一整条功率链。'),
('先看瞬时功率','起跑瞬间，系统需要的是短时间的大功率。电池要能稳定提供电流，母线、连接器和驱动器也要承受电压与电流变化。'),
('电机与电池','电池提供电能，逆变器把它变成电机可用的电流，电机再把电能变成扭矩。电压、电流、转速和温度共同决定输出边界。'),
('功率链路','从电芯到电池包，从保险与接触器到母线、驱动器和电机，每个环节都有电阻、损耗和保护策略。高功率会放大压降与发热。'),
('机械传动','电机扭矩还要经过减速器、关节轴承和连杆传到脚底。减速比是在速度、扭矩、效率、反驱性和寿命之间做取舍。'),
('结构也在消耗功率','机器人不仅搬运外部负载，还反复加速自己的腿、手臂和躯干。更重的结构可能更强，但也提高了惯量和峰值功率需求。'),
('热管理','短时爆发不等于持续工作。电机、功率器件和电池发热后，控制器可能降额；温度传感、热路径和散热能力决定系统能否重复运行。'),
('短时爆发 vs 可靠输出','一辆车能猛冲，不代表能连续爬坡。机器人同样如此：峰值速度是演示能力，持续、可重复、可预测的输出才是工程能力。'),
('系统工程结论','所以，冲刺速度是电机、控制和机械的共同成绩；持续可靠的速度，则是电池、功率链、热管理、结构和安全策略共同拿到的成绩。'),
]
key=os.environ['SILICONFLOW_API_KEY']; generate_images=os.environ.get('GENERATE_IMAGES') == '1'; srt=[]; concat=[]; t=0.0
image_style=('cinematic industrial robotics documentary, realistic engineering visualization, '
             'dark navy background with controlled orange energy highlights, clean composition, '
             'no text, no watermark, no logo, 16:9')
total_sections=len(sections)
def stamp(x):
    h=int(x//3600); m=int(x%3600//60); sec=x%60
    return f'{h:02d}:{m:02d}:{sec:06.3f}'.replace('.',',')
for i,(title,body) in enumerate(sections,1):
    prefix=f'[{i}/{total_sections}] {title}'
    print(f'{prefix}：生成配音…', flush=True)
    req=urllib.request.Request('https://api.siliconflow.cn/v1/audio/speech', data=json.dumps({'model':'FunAudioLLM/CosyVoice2-0.5B','voice':'FunAudioLLM/CosyVoice2-0.5B:alex','input':body,'response_format':'mp3','stream':False}).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    audio=build/f'{i:02d}.mp3'
    try:
        with urllib.request.urlopen(req, timeout=120) as r: audio.write_bytes(r.read())
    except Exception as e: raise SystemExit(f'硅基流动 TTS 失败（未输出密钥）：{e}')
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(audio)]))
    clip=build/f'{i:02d}.mp4'; color=['0x10233f','0x123b4a','0x26324d'][i%3]
    image=build/f'{i:02d}.png'
    if generate_images:
        print(f'{prefix}：生成 Qwen-Image 分镜图…', flush=True)
        prompt=f'{image_style}. Scene: {title}. Visualize: {body}'
        image_req=urllib.request.Request('https://api.siliconflow.cn/v1/images/generations', data=json.dumps({'model':'Qwen/Qwen-Image','prompt':prompt,'image_size':'1664x928','num_inference_steps':20,'cfg':4.0}).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(image_req, timeout=180) as r: image_url=json.load(r)['images'][0]['url']
            with urllib.request.urlopen(image_url, timeout=180) as r: image.write_bytes(r.read())
        except Exception as e: raise SystemExit(f'硅基流动 Qwen-Image 失败（未输出密钥）：{e}')
    print(f'{prefix}：渲染视频片段…', flush=True)
    if generate_images and image.exists():
        video_input=['-loop','1','-framerate','30','-i',str(image)]
        video_filter=['-vf','scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p','-t',str(dur)]
    else:
        video_input=['-f','lavfi','-i',f'color=c={color}:s=1920x1080:r=30:d={dur}']
        video_filter=['-pix_fmt','yuv420p']
    subprocess.run(['ffmpeg','-y','-v','error',*video_input,'-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264',*video_filter,'-c:a','aac','-shortest',str(clip)],check=True)
    concat.append(f"file '{clip}'")
    srt += [str(i),f'{stamp(t)} --> {stamp(t+dur)}',f'{title}：{body}','']; t+=dur
    print(f'{prefix}：完成（累计 {t:.1f}s）', flush=True)
(build/'concat.txt').write_text('\n'.join(concat)+'\n'); (build/'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')
print(f'全部 {total_sections} 个分镜完成，累计时长 {t:.1f}s。', flush=True)
