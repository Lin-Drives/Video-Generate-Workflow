import json, os, re, subprocess, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root, build = map(Path, sys.argv[1:]); out=root/'outputs'; build.mkdir(parents=True, exist_ok=True)
sections=[
('开场：冲刺的几秒','机器人冲刺时，到底是谁在出力？答案不是单独一台电机，而是一整条功率链。','在深蓝色背景下，聚光灯下的体育场百米跑道内，一台“荣耀闪电”人形机器人正在快速起跑冲刺，低机位，突出腿部执行器和关节，强烈的运动感。'),
('先看瞬时功率','起跑瞬间，系统需要的是短时间的大功率。电池要能稳定提供电流，母线、连接器和驱动器也要承受电压与电流变化。','“荣耀闪电”人形机器人用的高功率电池包、铜制母线和集成式的小型关节电机的近景特写，橙色能量光流沿着部件之间传递。'),
('电机与电池','电池提供电能，逆变器把它变成电机可用的电流，电机再把电能变成扭矩。电压、电流、转速和温度共同决定输出边界。','“荣耀闪电”人形机器人电池包、铜制母线与集成式小型关节电机的工程爆炸视图，三个部件以清晰的物理连接组成动力链路。'),
('功率链路','从电芯到电池包，从保险与接触器到母线、驱动器和电机，每个环节都有电阻、损耗和保护策略。高功率会放大压降与发热。','“荣耀闪电”人形机器人髋部传动到膝部传动的写实近景：体现高功率电气系统的集成化。'),
('机械传动','电机扭矩还要经过减速器、关节轴承和连杆传到脚底。减速比是在速度、扭矩、效率、反驱性和寿命之间做取舍。','“荣耀闪电”人形机器人腿部关节，包含行星齿轮减速器，局部透明剖视，展现机械传动路径。'),
('结构也在消耗功率','机器人不仅搬运外部负载，还反复加速自己的腿、手臂和躯干。更重的结构可能更强，但也提高了惯量和峰值功率需求。','“荣耀闪电”人形机器人处于迈步中段，关节式腿部、手臂和躯干结构清晰可见，表现质量与惯性带来的工程感。'),
('热管理','短时爆发不等于持续工作。电机、功率器件和电池发热后，控制器可能降额；温度传感、热路径和散热能力决定系统能否重复运行。','“荣耀闪电”人形机器人身上的几十个电机联动，写实工业画面，局部低调热力发光，能看到冷却板和气流散热结构。'),
('短时爆发 vs 可靠输出','一辆车能猛冲，不代表能连续爬坡。机器人同样如此：峰值速度是演示能力，持续、可重复、可预测的输出才是工程能力。','实验室内的“荣耀闪电”人形机器人正在斜坡上进行耐久测试，动作稳定可重复，背景为工业测试设备。'),
('系统工程结论','所以，冲刺速度是电机、控制和机械的共同成绩；持续可靠的速度，则是电池、功率链、热管理、结构和安全策略共同拿到的成绩。','不再是“荣耀闪电”这一款机器人，而是抽象为一个广义上的人形机器人，从背后往前看的视角，远处延伸的是更长的跑道，具有高级工程纪录片质感。'),
]
key=os.environ.get('SILICONFLOW_API_KEY'); generate_images=os.environ.get('GENERATE_IMAGES') == '1'; reuse_audio=os.environ.get('REUSE_AUDIO') == '1'; use_existing_images=os.environ.get('USE_EXISTING_IMAGES') == '1'; image_scenes={int(x) for x in os.environ.get('IMAGE_SCENES','').split(',') if x.strip()}; srt=[]; concat=[]; t=0.0
image_style='电影级中国“荣耀闪电”人形机器人工程纪录片，写实工程可视化，深蓝色背景，克制的橙色能量高光，构图干净。'
negative_prompt='任何文字、汉字、英文字母、数字、标签、标题、字幕、水印、标志、界面、信息图、图表、示意图、比例文字。'
total_sections=len(sections)
def stamp(x):
    h=int(x//3600); m=int(x%3600//60); sec=x%60
    return f'{h:02d}:{m:02d}:{sec:06.3f}'.replace('.',',')
def normalize_screen_text(text):
    """Keep on-screen Chinese punctuation consistent and remove noisy marks."""
    text=text.replace('：', '，')
    text=re.sub(r'[“”\"‘’]', '', text)
    text=re.sub(r'[,，]{2,}', '，', text)
    text=re.sub(r'[。！？；]{2,}', '。', text)
    return text.strip('， ')

def subtitle_chunks(text, maximum=29):
    """Prefer complete clauses; only split a sentence when it exceeds two short lines."""
    text=normalize_screen_text(text)
    chunks=[]
    sentences=re.findall(r'[^。！？；]+[。！？；]?', text)
    for sentence in sentences:
        if len(sentence) <= maximum:
            chunks.append(sentence)
            continue
        clauses=re.findall(r'[^，]+，?', sentence)
        current=''
        for clause in clauses:
            if len(current)+len(clause) <= maximum:
                current+=clause
            else:
                if current:
                    # Do not leave a short lead-in (for example, “持续可靠的速度，”)
                    # alone when a comma-list can complete that semantic unit.
                    room=maximum-len(current)
                    joins=[match.end() for match in re.finditer('、', clause) if match.end() <= room]
                    if len(current) <= 8 and joins:
                        split=joins[-1]
                        chunks.append(current+clause[:split])
                        current=clause[split:]
                        continue
                    chunks.append(current)
                current=clause
        if current:
            chunks.append(current)
    return chunks or [text]

def subtitle_image(text, path):
    canvas=Image.new('RGBA',(1920,1080),(0,0,0,0)); draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',42,index=0)
    lines=[]; line=''
    for char in text:
        candidate=line+char
        if draw.textbbox((0,0),candidate,font=font)[2] > 1320:
            lines.append(line); line=char
        else: line=candidate
    if line: lines.append(line)
    text='\n'.join(lines); box=draw.multiline_textbbox((0,0),text,font=font,spacing=12,align='center',stroke_width=2)
    width=box[2]-box[0]; height=box[3]-box[1]; x=(1920-width)//2; y=984-height
    draw.rounded_rectangle((x-30,y-16,x+width+30,y+height+16),radius=16,fill=(0,0,0,165))
    draw.multiline_text((x,y),text,font=font,fill='white',spacing=12,align='center',stroke_width=2,stroke_fill=(0,0,0,255))
    canvas.save(path)
for i,(title,body,visual) in enumerate(sections,1):
    prefix=f'[{i}/{total_sections}] {title}'
    audio=build/f'{i:02d}.mp3'
    if reuse_audio and audio.exists():
        print(f'{prefix}：复用已有配音…', flush=True)
    else:
        print(f'{prefix}：生成配音…', flush=True)
        req=urllib.request.Request('https://api.siliconflow.cn/v1/audio/speech', data=json.dumps({'model':'FunAudioLLM/CosyVoice2-0.5B','voice':'FunAudioLLM/CosyVoice2-0.5B:alex','input':body,'response_format':'mp3','stream':False}).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: audio.write_bytes(r.read())
        except Exception as e: raise SystemExit(f'硅基流动 TTS 失败（未输出密钥）：{e}')
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(audio)]))
    color=['0x10233f','0x123b4a','0x26324d'][i%3]
    image=build/f'{i:02d}.png'
    should_generate_image=generate_images and (not image_scenes or i in image_scenes)
    if should_generate_image:
        print(f'{prefix}：生成 Qwen-Image 分镜图…', flush=True)
        prompt=f'{image_style}. {visual}'
        image_req=urllib.request.Request('https://api.siliconflow.cn/v1/images/generations', data=json.dumps({'model':'Qwen/Qwen-Image','prompt':prompt,'negative_prompt':negative_prompt,'image_size':'1664x928','num_inference_steps':20,'cfg':4.0}).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(image_req, timeout=180) as r: image_url=json.load(r)['images'][0]['url']
            with urllib.request.urlopen(image_url, timeout=180) as r: image.write_bytes(r.read())
        except Exception as e: raise SystemExit(f'硅基流动 Qwen-Image 失败（未输出密钥）：{e}')
    elif use_existing_images and not image.exists:
        raise SystemExit(f'缺少已有分镜图：{image}；请移除 USE_EXISTING_IMAGES=1 或先生成图片。')
    print(f'{prefix}：按短句渲染字幕片段…', flush=True)
    chunks=subtitle_chunks(body)
    weights=[max(len(chunk), 8) for chunk in chunks]
    elapsed=0.0
    for j, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        segment=dur*weight/sum(weights) if j < len(chunks) else dur-elapsed
        subtitle=build/f'{i:02d}-{j:02d}-subtitle.png'; subtitle_image(chunk,subtitle)
        clip=build/f'{i:02d}-{j:02d}.mp4'
        if (generate_images or use_existing_images) and image.exists():
            video_input=['-loop','1','-framerate','30','-i',str(image)]
            filter_graph='[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[base];[base][1:v]overlay=0:0,format=yuv420p[v]'
        else:
            video_input=['-f','lavfi','-i',f'color=c={color}:s=1920x1080:r=30:d={segment}']
            filter_graph='[0:v][1:v]overlay=0:0,format=yuv420p[v]'
        subprocess.run(['ffmpeg','-y','-v','error',*video_input,'-loop','1','-framerate','30','-i',str(subtitle),'-ss',str(elapsed),'-t',str(segment),'-i',str(audio),'-filter_complex',filter_graph,'-map','[v]','-map','2:a','-c:v','libx264','-t',str(segment),'-c:a','aac','-shortest',str(clip)],check=True)
        concat.append(f"file '{clip}'")
        srt += [str(len(srt)//4+1),f'{stamp(t)} --> {stamp(t+segment)}',chunk,'']
        t+=segment; elapsed+=segment
    print(f'{prefix}：完成（累计 {t:.1f}s）', flush=True)
(build/'concat.txt').write_text('\n'.join(concat)+'\n'); (build/'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')
prompt_doc=['# Qwen-Image 分镜提示词', '', f'统一风格：{image_style}', f'负面提示词：{negative_prompt}', '']
for i,(title,_,visual) in enumerate(sections,1): prompt_doc += [f'## {i:02d} {title}', visual, '']
(out/'分镜提示词.md').write_text('\n'.join(prompt_doc), encoding='utf-8')
print(f'全部 {total_sections} 个分镜完成，累计时长 {t:.1f}s。', flush=True)
