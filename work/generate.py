# -*- coding: utf-8 -*-
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root, build = map(Path, sys.argv[1:]); out=root/'outputs'; build.mkdir(parents=True, exist_ok=True)
INTRO_DURATION=3.5; OUTRO_DURATION=5.0
sections=[
('开场：先回答我在哪','机器人进入真实世界开始工作之前，先要回答一个问题，我在哪。看见世界，是所有动作的起点。','空旷的半导体洁净室走廊内，这台白色硅片搬运机器人静立，底盘黑色传感器窗口透出微弱橙色光，车身侧面青绿色状态灯带亮起，表现启动前的观察与定位瞬间。'),
('摄像头：主感官','摄像头便宜、信息量大，是机器人的主感官。但照片是平的，近处的人和远处的墙，看起来只是大小不同。照片里只有颜色和亮度，距离要靠算法推出来。','这台硅片搬运机器人机身上视觉传感器的极近景特写：黑色内凹传感器窗口与机械臂腕部相机嵌在白色机身和深灰色手臂中，镜头镀膜反射出洁净室的灯光，突出眼睛的精密感。'),
('双目：像人眼一样测距','两个摄像头像人的双眼，靠两张照片的视差估算深度。但它怕暗、怕白墙，表面没有纹理，就算不出深度。','这台硅片搬运机器人以双目摄像头注视右侧开放式晶圆承载舱，两枚镜头朝向同一目标，画面聚焦在镜头与承载舱的对视关系上，表现被动观察的测距方式。'),
('激光雷达：主动发光测距','激光雷达不一样，它主动发光，靠光往返一趟的时间测距。一圈圈扫描下来，直接给出精确的三维点云。它不怕黑，但贵，也分不清颜色和纹理。','这台硅片搬运机器人在洁净室中缓缓转向，底盘的黑色激光雷达窗口正在扫描，周围空间中悬浮着由细密橙色光点组成的三维点云，点云自然贴合墙面、机台与地面轮廓，写实光影质感。'),
('多传感器融合','没有一种传感器是万能的。摄像头认得出物体，激光雷达量得准距离。把多种传感器对齐到同一个世界，才是真正的看见。','这台硅片搬运机器人在成排的白色工艺机台之间穿行，底盘雷达窗口与机身摄像头同时亮起，周围环境被一层极淡的暖色光晕覆盖，表现多源信息被整合成统一世界模型，画面克制不炫技。'),
('从像素到语义','认出画面里的东西，要靠一种叫神经网络的算法。它从海量照片里学会了认东西，把像素变成物体。这是门，那是台阶，前面有人。机器人要知道的不只是环境里有什么。还要判断能不能安全通行。要抓取的对象处在什么状态，能不能抓取。','这台硅片搬运机器人在一台工艺机台的上下料口前停下，顶部深灰色机械臂的夹爪悬停在对接位置前方，表现它正在分辨这是哪台机台和能不能对接的判断瞬间。'),
('实时性与算力','感知要在几十毫秒内完成，慢一拍就可能撞上。算力有限，看得清和算得快之间永远在取舍。','这台硅片搬运机器人在狭长洁净室走廊中快速行进，机械臂收拢在机身上方，背景机台有轻微运动模糊，而机器人本体与前方路径清晰锐利，表现感知系统在高速下仍然跟得上。'),
('失效与自知','强光、黑夜、遮挡、反光，都会让传感器失灵。好的系统不是从不出错，而是知道自己什么时候不可靠。','洁净室光刻区的强烈黄光下，这台硅片搬运机器人减速停住，光滑地面反射出大片眩光，传感器窗口亮度降低，青绿色状态灯带变为谨慎的暗色，表现感知不可靠时的自我保护。'),
('系统工程结论','所以看见不是一台相机的事。是传感器、算法、算力和安全策略的系统工程。感知越可靠，机器人的动作才敢越快。','抽象化的硅片搬运机器人背影，静立于洁净室中央，机械臂自然收拢，周身被稀疏的橙色点云与微光环绕，点云沿着成排机台向远处延伸融入深蓝背景，表现看见是系统工程的结论，高级工程纪录片质感。'),
]
key=os.environ.get('SILICONFLOW_API_KEY'); image_provider=os.environ.get('IMAGE_PROVIDER','gpt'); generate_images=os.environ.get('GENERATE_IMAGES') == '1'; reuse_audio=os.environ.get('REUSE_AUDIO') == '1'; use_existing_images=os.environ.get('USE_EXISTING_IMAGES') == '1'; image_scenes={int(x) for x in os.environ.get('IMAGE_SCENES','').split(',') if x.strip()}; srt=[]; concat=[]; t=0.0
gpt_assets=[
    '01-开场定位.png', '02-摄像头.png', '03-双目深度.png',
    '04-激光雷达.png', '05-多传感器融合.png', '06-像素到语义.png',
    '07-实时性.png', '08-失效与自知.png', '09-系统工程结论.png',
]
gpt_asset_dir='assets/ow12'
image_style='电影级半导体洁净室工程纪录片，写实工程可视化，洁净室的浅色环境与深蓝色氛围光形成对比，克制的橙色传感器高光，构图干净。'
negative_prompt='任何文字、汉字、英文字母、数字、标签、标题、字幕、水印、标志、界面、信息图、图表、示意图、比例文字。'
total_sections=len(sections)
if generate_images and image_provider != 'qwen':
    raise SystemExit('当前主配置为 GPT 生图：请先通过 GPT 图像工作流生成并审核分镜，再用 USE_EXISTING_IMAGES=1 渲染。Qwen 仅作为备选：IMAGE_PROVIDER=qwen GENERATE_IMAGES=1 ./render.sh')
english_subtitles=[
    'Before a robot enters the real world to work, it must first answer: where am I',
    'Seeing the world is the starting point of every action',
    'Cameras are cheap and information-rich: the robot\'s primary sense',
    'But a photo is flat: a person nearby and a far wall just differ in size',
    'A photo only records color and brightness; distance must be computed',
    'Two cameras work like human eyes, estimating depth from disparity',
    'But it struggles in the dark and on blank walls: no texture, no depth',
    'LiDAR is different: it emits light and times each round trip to measure distance',
    'Scanning round and round, it directly produces a precise 3D point cloud',
    'It works in the dark, but it is costly and cannot read color or texture',
    'No single sensor can do everything',
    'Cameras recognize objects; LiDAR measures distance accurately',
    'Aligning many sensors into one world is what seeing really means',
    'Recognizing what is in the frame takes an algorithm called a neural network',
    'Trained on massive numbers of photos, it learns to turn pixels into objects',
    'A door, a step, a person ahead',
    'It must know not just what is in the environment',
    'It must also judge whether it can pass safely',
    'And what state the grasp target is in, whether it can be grasped',
    'Perception must finish within tens of milliseconds; one beat late means a collision',
    'Compute is limited: seeing clearly and computing fast is a constant trade-off',
    'Glare, darkness, occlusion, and reflections can all blind a sensor',
    'A good system never assumes it is right; it knows when it is unreliable',
    'So seeing is not the job of a single camera',
    'It is system engineering across sensors, algorithms, compute, and safety',
    'The more reliable the perception, the faster the robot dares to move',
]
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

def screen_text(text):
    return text.rstrip('，。！？； ')

def subtitle_image(chinese, english, path):
    canvas=Image.new('RGBA',(1920,1080),(0,0,0,0)); draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',42,index=2)
    english_font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',27)
    text=screen_text(chinese); english=english.rstrip('.!?;:, ')
    lines=[]; line=''
    for char in text:
        candidate=line+char
        if draw.textbbox((0,0),candidate,font=font)[2] > 1320:
            lines.append(line); line=char
        else: line=candidate
    if line: lines.append(line)
    text='\n'.join(lines); box=draw.multiline_textbbox((0,0),text,font=font,spacing=12,align='center',stroke_width=2)
    en_box=draw.textbbox((0,0),english,font=english_font,stroke_width=1)
    width=max(box[2]-box[0], en_box[2]-en_box[0]); height=(box[3]-box[1])+(en_box[3]-en_box[1])+14; x=(1920-width)//2; y=972-height
    draw.rounded_rectangle((x-30,y-16,x+width+30,y+height+16),radius=16,fill=(0,0,0,165))
    draw.multiline_text((x,y),text,font=font,fill='white',spacing=12,align='center',stroke_width=2,stroke_fill=(0,0,0,255))
    draw.text(((1920-(en_box[2]-en_box[0]))//2, y+(box[3]-box[1])+14),english,font=english_font,fill=(220,225,232),stroke_width=1,stroke_fill=(0,0,0,220))
    canvas.save(path)

def title_card(chinese, english, path, cta=None):
    canvas=Image.new('RGBA',(1920,1080),(0,0,0,0)); draw=ImageDraw.Draw(canvas)
    cn_font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',64,index=2)
    en_font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',32)
    cta_font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',32,index=2)
    def centered(text, font, y, color):
        box=draw.textbbox((0,0),text,font=font); draw.text(((1920-(box[2]-box[0]))//2,y),text,font=font,fill=color,stroke_width=2,stroke_fill=(0,0,0,230))
    centered(chinese,cn_font,760,(255,255,255,255)); centered(english,en_font,844,(215,224,238,255))
    if cta: centered(cta,cta_font,936,(245,160,76,255))
    canvas.save(path)

def render_title_clip(background, overlay, clip, duration):
    # Match the CosyVoice clips exactly; concat demuxing cannot safely mix AAC formats.
    subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-framerate','30','-i',str(background),'-loop','1','-framerate','30','-i',str(overlay),'-f','lavfi','-i','anullsrc=channel_layout=mono:sample_rate=24000','-filter_complex',f'[0:v]scale=2020:1136,crop=1920:1080,fade=t=in:st=0:d=0.45,fade=t=out:st={duration-0.45}:d=0.45[base];[base][1:v]overlay=0:0,format=yuv420p[v]','-map','[v]','-map','2:a','-t',str(duration),'-c:v','libx264','-c:a','aac','-ar','24000','-ac','1','-shortest',str(clip)],check=True)

intro_overlay=build/'intro-title.png'; outro_overlay=build/'outro-title.png'
title_card('机器人怎么看见世界？','HOW DOES A ROBOT SEE THE WORLD?',intro_overlay)
render_title_clip(root/gpt_asset_dir/gpt_assets[0], intro_overlay, build/'intro.mp4', INTRO_DURATION)
title_card('感知越可靠，动作才敢越快','THE BETTER IT SEES, THE FASTER IT DARES',outro_overlay,'关注获取更多工程拆解')
render_title_clip(root/gpt_asset_dir/gpt_assets[-1], outro_overlay, build/'outro.mp4', OUTRO_DURATION)
concat.append(f"file '{build/'intro.mp4'}"); t=INTRO_DURATION
translation_index=0
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
    qwen_image=build/f'{i:02d}.png'
    image=(root/gpt_asset_dir/gpt_assets[i-1]) if image_provider == 'gpt' else qwen_image
    should_generate_image=generate_images and (not image_scenes or i in image_scenes)
    if should_generate_image:
        print(f'{prefix}：生成备选 Qwen-Image 分镜图…', flush=True)
        prompt=f'{image_style}. {visual}'
        image_req=urllib.request.Request('https://api.siliconflow.cn/v1/images/generations', data=json.dumps({'model':'Qwen/Qwen-Image','prompt':prompt,'negative_prompt':negative_prompt,'image_size':'1664x928','num_inference_steps':20,'cfg':4.0}).encode(), headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(image_req, timeout=180) as r: image_url=json.load(r)['images'][0]['url']
            with urllib.request.urlopen(image_url, timeout=180) as r: qwen_image.write_bytes(r.read())
        except Exception as e: raise SystemExit(f'硅基流动 Qwen-Image 失败（未输出密钥）：{e}')
    elif use_existing_images and not image.exists():
        raise SystemExit(f'缺少已有分镜图：{image}；请移除 USE_EXISTING_IMAGES=1 或先生成图片。')
    print(f'{prefix}：按短句渲染字幕片段…', flush=True)
    chunks=subtitle_chunks(body)
    weights=[max(len(chunk), 8) for chunk in chunks]
    elapsed=0.0
    for j, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        segment=dur*weight/sum(weights) if j < len(chunks) else dur-elapsed
        if translation_index >= len(english_subtitles):
            raise SystemExit('英文字幕条目数量与中文意群不一致')
        english=english_subtitles[translation_index]; translation_index+=1
        subtitle=build/f'{i:02d}-{j:02d}-subtitle.png'; subtitle_image(chunk,english,subtitle)
        clip=build/f'{i:02d}-{j:02d}.mp4'
        if (generate_images or use_existing_images) and image.exists():
            video_input=['-loop','1','-framerate','30','-i',str(image)]
            filter_graph='[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[base];[base][1:v]overlay=0:0,format=yuv420p[v]'
        else:
            video_input=['-f','lavfi','-i',f'color=c={color}:s=1920x1080:r=30:d={segment}']
            filter_graph='[0:v][1:v]overlay=0:0,format=yuv420p[v]'
        subprocess.run(['ffmpeg','-y','-v','error',*video_input,'-loop','1','-framerate','30','-i',str(subtitle),'-ss',str(elapsed),'-t',str(segment),'-i',str(audio),'-filter_complex',filter_graph,'-map','[v]','-map','2:a','-c:v','libx264','-t',str(segment),'-c:a','aac','-shortest',str(clip)],check=True)
        concat.append(f"file '{clip}'")
        srt += [str(len(srt)//4+1),f'{stamp(t)} --> {stamp(t+segment)}',f'{screen_text(chunk)}\n{english.rstrip(".!?;:, ")}', '']
        t+=segment; elapsed+=segment
    print(f'{prefix}：完成（累计 {t:.1f}s）', flush=True)
concat.append(f"file '{build/'outro.mp4'}")
if translation_index != len(english_subtitles): raise SystemExit('英文字幕存在未使用条目')
(build/'concat.txt').write_text('\n'.join(concat)+'\n'); (build/'subtitles.srt').write_text('\n'.join(srt), encoding='utf-8')
prompt_doc=['# GPT 图像工作流分镜提示词：机器人怎么"看见"世界？', '', '主配置：GPT 图像工作流；Qwen 仅作备选。', '素材来源：assets/优艾智合1.png 至 assets/优艾智合4.png，以及 assets/ow12-300-无托盘-角色参考.png（无硅片托盘主参考），即优艾智合（YOUIBOT）OW12-300 十二寸晶圆搬运移动操作机器人的官方素材。外观要点：下层为扁平、长方形的白色移动底盘，四角和侧面有细绿色状态灯带、黑色防撞边与前部黑色传感器窗口；上层是白色箱体，中部为倾斜控制面板，右侧是无托盘时可见的开放式方形晶圆承载舱、底部导轨和悬臂平台；顶部通过短立柱连接深灰色六轴协作机械臂，末端为银色金属夹爪。生图时严格以无托盘主参考为准：不得画成立式柜体、单一梯形底盘、透明晶圆盒陈列柜或黑色 FOUP。', '动态镜头准入：本片为轮式底盘，无步态问题，但行进镜头必须人工检查上下双层底盘的比例与透视、轮子与地面的接触关系、机械臂与顶部立柱的连接位置、右侧开放式承载舱和导轨结构是否合理；含点云、光锥等可视化元素时，必须保持其像物理光影而非屏幕图形，避免落入示意图风格。', f'统一风格：{image_style}', f'负面提示词：{negative_prompt}', '']
for i,(title,_,visual) in enumerate(sections,1): prompt_doc += [f'## {i:02d} {title}', visual, '']
(out/'分镜提示词-感知与视觉.md').write_text('\n'.join(prompt_doc), encoding='utf-8')
print(f'全部 {total_sections} 个分镜完成，累计时长 {t:.1f}s。', flush=True)
