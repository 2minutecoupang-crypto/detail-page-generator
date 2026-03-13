from flask import Flask, request, jsonify, send_file, render_template_from_string
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import requests
import anthropic
import io
import base64
import os
import json
import urllib.request
import tempfile

app = Flask(__name__)
CORS(app)

HTML_PAGE = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>상세페이지 자동 생성기</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#0f0f0f;--surface:#1a1a1a;--border:#2e2e2e;--accent:#ff4757;--text:#f0f0f0;--text2:#888;--text3:#444;--radius:12px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Sans KR",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{padding:18px 28px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg);z-index:100}
.logo{font-size:16px;font-weight:900;letter-spacing:-.03em;display:flex;align-items:center;gap:8px}
.logo-dot{width:8px;height:8px;background:var(--accent);border-radius:50%}
.api-btn{font-size:12px;padding:7px 14px;border:1px solid var(--border);border-radius:8px;background:transparent;color:var(--text2);cursor:pointer;font-family:inherit}
.api-btn:hover{border-color:var(--accent);color:var(--accent)}
.layout{display:flex;height:calc(100vh - 57px)}
.left{width:360px;min-width:360px;border-right:1px solid var(--border);overflow-y:auto;padding:20px}
.right{flex:1;overflow-y:auto;background:#111;display:flex;flex-direction:column}
.lbl{font-size:10px;font-weight:700;letter-spacing:.1em;color:var(--text3);text-transform:uppercase;margin-bottom:8px;margin-top:20px}
.lbl:first-child{margin-top:0}
.upload-zone{border:1.5px dashed var(--border);border-radius:var(--radius);padding:24px 16px;text-align:center;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.upload-zone:hover{border-color:var(--accent)}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.upload-zone.has-image{padding:0;border-style:solid}
.upload-zone.has-image img{width:100%;border-radius:10px;display:block;max-height:180px;object-fit:contain;background:#fff}
input[type=text],textarea,input[type=password]{width:100%;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13px;color:var(--text);font-family:inherit;transition:border-color .2s;outline:none}
input[type=text]:focus,textarea:focus,input[type=password]:focus{border-color:var(--accent)}
textarea{resize:vertical;min-height:68px;line-height:1.6}
.gap{margin-bottom:7px}
.feat-row{display:flex;gap:6px;margin-bottom:6px;align-items:center}
.feat-row input{flex:1}
.del-btn{width:28px;height:28px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--text3);cursor:pointer;font-size:15px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.del-btn:hover{border-color:var(--accent);color:var(--accent)}
.add-link{font-size:12px;color:var(--accent);background:none;border:none;cursor:pointer;padding:3px 0;font-family:inherit}
.generate-btn{width:100%;margin-top:20px;padding:14px;background:var(--accent);color:white;border:none;border-radius:var(--radius);font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;transition:all .2s}
.generate-btn:hover{background:#e03e4e;transform:translateY(-1px)}
.generate-btn:disabled{background:var(--surface);color:var(--text3);cursor:not-allowed;transform:none}
.status-bar{display:none;margin-top:14px;padding:14px 16px;background:var(--surface);border-radius:8px;border-left:3px solid var(--accent)}
.status-bar.visible{display:block}
.s-step{display:flex;align-items:center;gap:8px;margin-bottom:7px;font-size:12px;color:var(--text2)}
.s-step:last-child{margin-bottom:0}
.s-dot{width:7px;height:7px;border-radius:50%;background:var(--border);flex-shrink:0;transition:background .3s}
.s-dot.done{background:#2ed573}
.s-dot.active{background:var(--accent);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.preview-wrap{flex:1;display:flex;align-items:flex-start;justify-content:center;padding:28px 20px}
.preview-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;min-height:400px;color:var(--text3);font-size:14px;text-align:center;gap:10px}
.preview-img{max-width:500px;width:100%;border-radius:16px;box-shadow:0 0 80px rgba(0,0,0,.6)}
.dl-wrap{padding:14px 20px;background:var(--bg);border-top:1px solid var(--border);display:none}
.dl-wrap.visible{display:flex;gap:8px}
.dl-btn{flex:1;padding:12px;background:#2ed573;color:#071a0f;border:none;border-radius:var(--radius);font-size:13px;font-weight:700;cursor:pointer;font-family:inherit}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:200;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:26px;width:400px;max-width:90vw}
.modal h2{font-size:15px;font-weight:700;margin-bottom:4px}
.modal p{font-size:12px;color:var(--text2);margin-bottom:18px;line-height:1.6}
.modal-field{margin-bottom:12px}
.modal-lbl{font-size:11px;font-weight:600;color:var(--text2);margin-bottom:5px;letter-spacing:.05em}
.api-note{font-size:11px;color:var(--text3);margin-top:3px}
.modal-actions{display:flex;gap:8px;margin-top:18px}
.modal-save{flex:1;padding:10px;background:var(--accent);color:white;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.modal-cancel{padding:10px 18px;background:transparent;border:1px solid var(--border);border-radius:8px;font-size:13px;color:var(--text2);cursor:pointer;font-family:inherit}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>
<div class="header">
  <div class="logo"><div class="logo-dot"></div>상세페이지 자동 생성기</div>
  <button class="api-btn" onclick="openModal()">⚙ API 키 설정</button>
</div>
<div class="layout">
  <div class="left">
    <div class="lbl">제품 이미지</div>
    <div class="upload-zone" id="uploadZone">
      <input type="file" accept="image/*" onchange="handleImage(event)" />
      <div id="uploadInner">
        <div style="font-size:26px;margin-bottom:7px">📦</div>
        <div style="font-size:13px;color:#888">제품 사진 1장 업로드</div>
        <div style="font-size:11px;color:#444;margin-top:4px">흰 배경 사진 권장</div>
      </div>
    </div>
    <div class="lbl">기본 정보</div>
    <div class="gap"><input type="text" id="pName" placeholder="제품명" /></div>
    <div class="gap"><input type="text" id="pCategory" placeholder="카테고리 (예: 마사지용품, 안전용품)" /></div>
    <div class="gap"><input type="text" id="pTarget" placeholder="타겟 고객 (예: 30~50대 여성, 아이 있는 부모)" /></div>
    <div class="lbl">핵심 특징</div>
    <div id="features">
      <div class="feat-row"><input type="text" placeholder="특징 1" /></div>
      <div class="feat-row"><input type="text" placeholder="특징 2" /></div>
      <div class="feat-row"><input type="text" placeholder="특징 3" /></div>
    </div>
    <button class="add-link" onclick="addFeature()">+ 특징 추가</button>
    <div class="lbl">제품 스펙 (선택)</div>
    <div id="specs">
      <div class="feat-row">
        <input type="text" placeholder="항목" style="width:36%;flex:none" />
        <input type="text" placeholder="값" style="flex:1" />
      </div>
    </div>
    <button class="add-link" onclick="addSpec()">+ 스펙 추가</button>
    <div class="lbl">추가 요청 (선택)</div>
    <textarea id="pExtra" placeholder="예: 고급스러운 톤, 선물용 강조 등"></textarea>
    <button class="generate-btn" id="genBtn" onclick="generate()">✦ 상세페이지 자동 생성</button>
    <div class="status-bar" id="statusBar">
      <div class="s-step"><div class="s-dot" id="d1"></div><span>카피 문구 생성 중...</span></div>
      <div class="s-step"><div class="s-dot" id="d2"></div><span>배경 이미지 생성 중...</span></div>
      <div class="s-step"><div class="s-dot" id="d3"></div><span>이미지 합성 중...</span></div>
      <div class="s-step"><div class="s-dot" id="d4"></div><span>완성!</span></div>
    </div>
  </div>
  <div class="right" id="rightPanel">
    <div class="preview-wrap" id="previewWrap">
      <div class="preview-placeholder">
        <div style="font-size:44px;opacity:.2">🖼</div>
        <div>제품 정보를 입력하고<br>생성 버튼을 눌러주세요</div>
      </div>
    </div>
    <div class="dl-wrap" id="dlWrap">
      <button class="dl-btn" onclick="downloadImg()">↓ JPG 이미지 저장</button>
    </div>
  </div>
</div>
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <h2>API 키 설정</h2>
    <p>한 번 입력하면 세션 동안 저장됩니다.</p>
    <div class="modal-field">
      <div class="modal-lbl">ANTHROPIC API KEY (필수)</div>
      <input type="password" id="apiAnthropic" placeholder="sk-ant-..." />
      <div class="api-note">→ console.anthropic.com → API Keys</div>
    </div>
    <div class="modal-field">
      <div class="modal-lbl">OPENAI API KEY (선택 — 배경 이미지)</div>
      <input type="password" id="apiOpenai" placeholder="sk-proj-..." />
      <div class="api-note">→ platform.openai.com → API keys</div>
    </div>
    <div class="modal-actions">
      <button class="modal-cancel" onclick="closeModal()">취소</button>
      <button class="modal-save" onclick="saveKeys()">저장</button>
    </div>
  </div>
</div>
<script>
let productImgB64=null;
let resultImgUrl=null;
let keys={anthropic:"",openai:""};
try{const s=JSON.parse(sessionStorage.getItem("dpkeys")||"{}");keys={...keys,...s};if(keys.anthropic)document.getElementById("apiAnthropic").value=keys.anthropic;if(keys.openai)document.getElementById("apiOpenai").value=keys.openai}catch(e){}
function openModal(){document.getElementById("modalOverlay").classList.add("open")}
function closeModal(){document.getElementById("modalOverlay").classList.remove("open")}
function saveKeys(){keys.anthropic=document.getElementById("apiAnthropic").value.trim();keys.openai=document.getElementById("apiOpenai").value.trim();try{sessionStorage.setItem("dpkeys",JSON.stringify(keys))}catch(e){}closeModal();toast("API 키 저장됨")}
document.getElementById("modalOverlay").addEventListener("click",e=>{if(e.target===e.currentTarget)closeModal()});
function handleImage(e){const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=ev=>{productImgB64=ev.target.result;const z=document.getElementById("uploadZone");z.classList.add("has-image");z.innerHTML=`<input type="file" accept="image/*" onchange="handleImage(event)" /><img src="${ev.target.result}" />`};r.readAsDataURL(f)}
function addFeature(){const d=document.getElementById("features");const n=d.children.length+1;const row=document.createElement("div");row.className="feat-row";row.innerHTML=`<input type="text" placeholder="특징 ${n}" /><button class="del-btn" onclick="this.parentElement.remove()">×</button>`;d.appendChild(row)}
function addSpec(){const d=document.getElementById("specs");const row=document.createElement("div");row.className="feat-row";row.innerHTML=`<input type="text" placeholder="항목" style="width:36%;flex:none" /><input type="text" placeholder="값" style="flex:1" /><button class="del-btn" onclick="this.parentElement.remove()">×</button>`;d.appendChild(row)}
function getInputs(){const features=Array.from(document.querySelectorAll("#features input")).map(i=>i.value).filter(v=>v.trim());const specs=Array.from(document.querySelectorAll("#specs .feat-row")).map(r=>{const ins=r.querySelectorAll("input");return ins[0]&&ins[1]?{k:ins[0].value,v:ins[1].value}:null}).filter(s=>s&&s.k&&s.v);return{name:document.getElementById("pName").value.trim(),category:document.getElementById("pCategory").value.trim(),target:document.getElementById("pTarget").value.trim(),features,specs,extra:document.getElementById("pExtra").value.trim()}}
function setStep(n){["d1","d2","d3","d4"].forEach((id,i)=>{const el=document.getElementById(id);if(i+1<n)el.className="s-dot done";else if(i+1===n)el.className="s-dot active";else el.className="s-dot"})}
async function generate(){
  const inp=getInputs();
  if(!inp.name){toast("제품명을 입력해주세요",true);return}
  if(!keys.anthropic){openModal();return}
  const btn=document.getElementById("genBtn");
  btn.disabled=true;btn.textContent="생성 중...";
  document.getElementById("statusBar").classList.add("visible");
  setStep(1);
  try{
    const fd=new FormData();
    fd.append("data",JSON.stringify({...inp,anthropic_key:keys.anthropic,openai_key:keys.openai}));
    if(productImgB64){const blob=await(await fetch(productImgB64)).blob();fd.append("image",blob,"product.jpg")}
    setStep(2);
    const res=await fetch("/generate",{method:"POST",body:fd});
    setStep(3);
    if(!res.ok){const e=await res.json();throw new Error(e.error||"서버 오류")}
    const blob=await res.blob();
    setStep(4);
    resultImgUrl=URL.createObjectURL(blob);
    document.getElementById("previewWrap").innerHTML=`<img class="preview-img" src="${resultImgUrl}" />`;
    document.getElementById("dlWrap").classList.add("visible");
    document.getElementById("statusBar").classList.remove("visible");
    btn.disabled=false;btn.textContent="✦ 다시 생성하기";
  }catch(err){
    btn.disabled=false;btn.textContent="✦ 상세페이지 자동 생성";
    document.getElementById("statusBar").classList.remove("visible");
    toast("오류: "+err.message,true);
  }
}
function downloadImg(){if(!resultImgUrl)return;const a=document.createElement("a");a.href=resultImgUrl;a.download=document.getElementById("pName").value+"_상세페이지.jpg";a.click()}
function toast(msg,err=false){const t=document.createElement("div");t.style.cssText=`position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:${err?"#ff4757":"#2ed573"};color:${err?"white":"#071a0f"};padding:10px 20px;border-radius:8px;font-size:13px;font-weight:700;z-index:999;font-family:inherit;white-space:nowrap`;t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}
</script>
</body>
</html>'''

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"

def get_font(size, bold=False):
    font_path = "/tmp/NotoSansKR.ttf"
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(
                "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf",
                font_path
            )
        except:
            return ImageFont.load_default()
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.ellipse([x1, y1, x1+2*radius, y1+2*radius], fill=fill)
    draw.ellipse([x2-2*radius, y1, x2, y1+2*radius], fill=fill)
    draw.ellipse([x1, y2-2*radius, x1+2*radius, y2], fill=fill)
    draw.ellipse([x2-2*radius, y2-2*radius, x2, y2], fill=fill)

def wrap_text(text, font, max_width, draw):
    lines = []
    if '\n' in text:
        for paragraph in text.split('\n'):
            lines.extend(wrap_text(paragraph, font, max_width, draw))
        return lines
    words = text.split()
    current_line = ""
    for word in words:
        test_line = current_line + ("" if not current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]

def draw_multiline(draw, text, x, y, font, fill, max_width, line_height=1.4, align="left"):
    lines = wrap_text(text, font, max_width, draw)
    total_h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lh = bbox[3] - bbox[1]
        if align == "center":
            lw = bbox[2] - bbox[0]
            draw.text((x - lw//2, y + total_h), line, font=font, fill=fill)
        else:
            draw.text((x, y + total_h), line, font=font, fill=fill)
        total_h += int(lh * line_height)
    return total_h

def generate_image(copy_data, product_img_bytes, bg_img_bytes, accent_color, bg_color):
    W = 800
    pad = 48
    inner_w = W - pad * 2
    
    ac = hex_to_rgb(accent_color)
    bg = hex_to_rgb(bg_color)
    white = (255, 255, 255)
    dark = (26, 26, 26)
    gray = (102, 102, 102)
    light_gray = (245, 245, 245)
    divider_color = (235, 235, 235)

    sections = []

    # ── SECTION 1: HERO ──
    hero_h = 380
    hero = Image.new('RGB', (W, hero_h), bg)
    d = ImageDraw.Draw(hero)

    # badges
    badge_y = 44
    badges = copy_data.get('badges', [])
    bx = pad
    for badge in badges[:2]:
        try:
            bf = get_font(20, bold=True)
            bbox = d.textbbox((0,0), badge, font=bf)
            bw = bbox[2]-bbox[0]+28
            bh = 36
            draw_rounded_rect(d, [bx, badge_y, bx+bw, badge_y+bh], 18, ac)
            d.text((bx+14, badge_y+8), badge, font=bf, fill=white)
            bx += bw + 10
        except:
            pass

    # hero title
    title = copy_data.get('hero_title', '').replace('\\n', '\n')
    try:
        tf = get_font(52, bold=True)
        ty = badge_y + 54
        lines = title.split('\n')
        for line in lines:
            bbox = d.textbbox((0,0), line, font=tf)
            lw = bbox[2]-bbox[0]
            d.text(((W-lw)//2, ty), line, font=tf, fill=dark)
            ty += int((bbox[3]-bbox[1])*1.25)
    except:
        pass

    # hero sub
    sub = copy_data.get('hero_sub', '')
    try:
        sf = get_font(26)
        bbox = d.textbbox((0,0), sub, font=sf)
        sw = bbox[2]-bbox[0]
        d.text(((W-sw)//2, ty+16), sub, font=sf, fill=gray)
        ty += int((bbox[3]-bbox[1])) + 32
    except:
        pass

    # stats
    stats = copy_data.get('stats', [])
    if stats:
        stat_y = hero_h - 90
        d.line([(pad, stat_y-12), (W-pad, stat_y-12)], fill=divider_color, width=1)
        sw_each = inner_w // len(stats)
        for i, stat in enumerate(stats):
            sx = pad + i * sw_each + sw_each//2
            try:
                vf = get_font(36, bold=True)
                lf = get_font(20)
                vbbox = d.textbbox((0,0), stat['val'], font=vf)
                vw = vbbox[2]-vbbox[0]
                d.text((sx-vw//2, stat_y), stat['val'], font=vf, fill=ac)
                lbbox = d.textbbox((0,0), stat['lbl'], font=lf)
                lw = lbbox[2]-lbbox[0]
                d.text((sx-lw//2, stat_y+44), stat['lbl'], font=lf, fill=gray)
            except:
                pass
            if i < len(stats)-1:
                d.line([(pad + (i+1)*sw_each, stat_y), (pad + (i+1)*sw_each, stat_y+70)], fill=divider_color, width=1)

    sections.append(hero)

    # ── SECTION 2: PRODUCT IMAGE ──
    if product_img_bytes:
        try:
            prod_img = Image.open(io.BytesIO(product_img_bytes)).convert('RGBA')
            prod_bg = Image.new('RGB', (W, 360), bg)
            max_size = 300
            prod_img.thumbnail((max_size, max_size), Image.LANCZOS)
            pw, ph = prod_img.size
            px = (W - pw) // 2
            py = (360 - ph) // 2
            prod_bg.paste(prod_img, (px, py), prod_img)
            sections.append(prod_bg)
        except Exception as e:
            pass

    # ── DIVIDER ──
    div = Image.new('RGB', (W, 12), light_gray)
    sections.append(div)

    # ── SECTION 3: PAIN ──
    pains = copy_data.get('pains', [])
    pain_h = 80 + len(pains) * 110 + 40
    pain_sec = Image.new('RGB', (W, pain_h), white)
    d = ImageDraw.Draw(pain_sec)

    pain_label = copy_data.get('pain_label', '')
    pain_title = copy_data.get('pain_title', '').replace('\\n', '\n')

    try:
        plf = get_font(22, bold=True)
        d.text((pad, 36), pain_label, font=plf, fill=ac)
        ptf = get_font(44, bold=True)
        ty = 70
        for line in pain_title.split('\n'):
            d.text((pad, ty), line, font=ptf, fill=dark)
            bbox = d.textbbox((0,0), line, font=ptf)
            ty += int((bbox[3]-bbox[1])*1.25)
    except:
        ty = 120

    for i, pain in enumerate(pains):
        py_start = ty + 20 + i * 110
        # card bg
        draw_rounded_rect(d, [pad, py_start, W-pad, py_start+88], 12,
                          tuple(min(255, c+230) for c in ac) if max(ac) < 200 else (255, 245, 248))
        # accent bar
        d.rectangle([pad, py_start, pad+4, py_start+88], fill=ac)
        try:
            tf2 = get_font(26, bold=True)
            df2 = get_font(22)
            d.text((pad+20, py_start+14), pain.get('title',''), font=tf2, fill=ac)
            draw_multiline(d, pain.get('desc',''), pad+20, py_start+46, df2, gray, inner_w-30)
        except:
            pass

    sections.append(pain_sec)
    sections.append(Image.new('RGB', (W, 12), light_gray))

    # ── SECTION 4: LIFESTYLE BG IMAGE ──
    if bg_img_bytes:
        try:
            bg_img = Image.open(io.BytesIO(bg_img_bytes)).convert('RGB')
            bg_img = bg_img.resize((W, 240), Image.LANCZOS)
            # overlay
            overlay = Image.new('RGBA', (W, 240), (0, 0, 0, 100))
            bg_img_rgba = bg_img.convert('RGBA')
            bg_img_rgba.paste(overlay, mask=overlay)
            bg_final = bg_img_rgba.convert('RGB')
            d_bg = ImageDraw.Draw(bg_final)
            ls_text = copy_data.get('lifestyle_text', '').replace('\\n', '\n')
            try:
                lsf = get_font(40, bold=True)
                lines = ls_text.split('\n')
                total_h = len(lines) * 56
                sy = (240 - total_h) // 2
                for line in lines:
                    bbox = d_bg.textbbox((0,0), line, font=lsf)
                    lw = bbox[2]-bbox[0]
                    d_bg.text(((W-lw)//2, sy), line, font=lsf, fill=white)
                    sy += 56
            except:
                pass
            sections.append(bg_final)
            sections.append(Image.new('RGB', (W, 12), light_gray))
        except:
            pass

    # ── SECTION 5: FEATURES ──
    features = copy_data.get('features', [])
    feat_h = 100 + len(features) * 160
    feat_sec = Image.new('RGB', (W, feat_h), white)
    d = ImageDraw.Draw(feat_sec)

    feat_title = copy_data.get('feature_title', '').replace('\\n', '\n')
    try:
        ftf = get_font(44, bold=True)
        ty = 40
        for line in feat_title.split('\n'):
            bbox = d.textbbox((0,0), line, font=ftf)
            lw = bbox[2]-bbox[0]
            d.text(((W-lw)//2, ty), line, font=ftf, fill=dark)
            ty += int((bbox[3]-bbox[1])*1.25)
    except:
        ty = 100

    for i, feat in enumerate(features):
        fy = ty + 20 + i * 160
        # card
        d.rectangle([pad, fy, W-pad, fy+130], fill=white, outline=divider_color, width=1)
        draw_rounded_rect(d, [pad, fy, W-pad, fy+130], 14, (252, 252, 252))
        d.rectangle([pad, fy, W-pad, fy+130], outline=divider_color, width=1)
        # icon box
        draw_rounded_rect(d, [pad+16, fy+20, pad+70, fy+74], 12, bg)
        try:
            icon_f = get_font(32)
            icon = feat.get('icon', '✦')
            ibbox = d.textbbox((0,0), icon, font=icon_f)
            iw = ibbox[2]-ibbox[0]
            d.text((pad+16+(54-iw)//2, fy+28), icon, font=icon_f, fill=ac)
        except:
            pass
        try:
            nf = get_font(20, bold=True)
            tf3 = get_font(30, bold=True)
            df3 = get_font(22)
            d.text((pad+88, fy+18), feat.get('num',''), font=nf, fill=ac)
            d.text((pad+88, fy+42), feat.get('title',''), font=tf3, fill=dark)
            draw_multiline(d, feat.get('desc',''), pad+88, fy+80, df3, gray, inner_w-100)
        except:
            pass

    sections.append(feat_sec)
    sections.append(Image.new('RGB', (W, 12), light_gray))

    # ── SECTION 6: CTA ──
    cta_h = 200
    cta_sec = Image.new('RGB', (W, cta_h), ac)
    d = ImageDraw.Draw(cta_sec)
    cta_title = copy_data.get('cta_title', '').replace('\\n', '\n')
    cta_sub = copy_data.get('cta_sub', '')
    try:
        ctf = get_font(44, bold=True)
        csf = get_font(24)
        ty = 36
        for line in cta_title.split('\n'):
            bbox = d.textbbox((0,0), line, font=ctf)
            lw = bbox[2]-bbox[0]
            d.text(((W-lw)//2, ty), line, font=ctf, fill=white)
            ty += int((bbox[3]-bbox[1])*1.3)
        bbox = d.textbbox((0,0), cta_sub, font=csf)
        lw = bbox[2]-bbox[0]
        d.text(((W-lw)//2, ty+8), cta_sub, font=csf, fill=(255,255,255,180))
    except:
        pass
    sections.append(cta_sec)

    # ── COMBINE ALL ──
    total_h = sum(s.size[1] for s in sections)
    final = Image.new('RGB', (W, total_h), white)
    y_offset = 0
    for sec in sections:
        final.paste(sec, (0, y_offset))
        y_offset += sec.size[1]

    output = io.BytesIO()
    final.save(output, format='JPEG', quality=92, optimize=True)
    output.seek(0)
    return output

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = json.loads(request.form.get('data', '{}'))
        anthropic_key = data.pop('anthropic_key', '')
        openai_key = data.pop('openai_key', '')

        if not anthropic_key:
            return jsonify({'error': 'Anthropic API 키가 없습니다'}), 400

        # ── 1. Generate copy ──
        client = anthropic.Anthropic(api_key=anthropic_key)
        prompt = f"""대한민국 최고의 쿠팡 상세페이지 카피라이터입니다.
아래 정보로 카피를 작성하고 순수 JSON만 반환하세요.

제품명: {data.get('name','')}
카테고리: {data.get('category','')}
타겟: {data.get('target','')}
특징: {', '.join(data.get('features',[]))}
추가요청: {data.get('extra','')}

반환 JSON:
{{
  "hero_title": "메인 헤드라인 2줄, \\n으로 줄바꿈",
  "hero_sub": "서브 카피 1줄",
  "badges": ["뱃지1","뱃지2"],
  "stats": [{{"val":"임팩트숫자","lbl":"설명"}},{{"val":"...","lbl":"..."}},{{"val":"...","lbl":"..."}}],
  "pain_label": "페인포인트 작은 레이블",
  "pain_title": "공감형 헤드라인 2줄, \\n으로 줄바꿈",
  "pains": [{{"title":"불편함제목","desc":"설명1~2문장"}},{{"title":"...","desc":"..."}},{{"title":"...","desc":"..."}}],
  "lifestyle_text": "이미지 위 문구 1~2줄, \\n으로 줄바꿈",
  "feature_title": "특징 섹션 헤드라인 2줄, \\n으로 줄바꿈",
  "features": [{{"num":"POINT 01","icon":"이모지","title":"특징제목","desc":"설명2~3문장"}},{{"num":"POINT 02","icon":"이모지","title":"...","desc":"..."}},{{"num":"POINT 03","icon":"이모지","title":"...","desc":"..."}}],
  "cta_title": "CTA 2줄, \\n으로 줄바꿈",
  "cta_sub": "CTA 서브",
  "accent_color": "#E05C7A",
  "bg_color": "#FFF0F4",
  "bg_prompt": "DALL-E 3 English prompt: beautiful lifestyle background scene for this product, no products visible, soft natural light, bokeh, commercial photography, 4k. Under 50 words."
}}"""

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        text = text.replace('```json','').replace('```','').strip()
        s = text.find('{'); e = text.rfind('}')
        if s != -1 and e != -1:
            text = text[s:e+1]
        copy_data = json.loads(text)

        accent_color = copy_data.get('accent_color', '#E05C7A')
        bg_color = copy_data.get('bg_color', '#FFF0F4')

        # ── 2. Generate background image ──
        bg_img_bytes = None
        if openai_key and copy_data.get('bg_prompt'):
            try:
                resp = requests.post(
                    'https://api.openai.com/v1/images/generations',
                    headers={'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'},
                    json={'model': 'dall-e-3', 'prompt': copy_data['bg_prompt'], 'n': 1, 'size': '1792x1024', 'quality': 'hd'},
                    timeout=60
                )
                if resp.ok:
                    img_url = resp.json()['data'][0]['url']
                    bg_img_bytes = requests.get(img_url, timeout=30).content
            except:
                pass

        # ── 3. Get product image ──
        product_img_bytes = None
        if 'image' in request.files:
            product_img_bytes = request.files['image'].read()

        # ── 4. Compose image ──
        result = generate_image(copy_data, product_img_bytes, bg_img_bytes, accent_color, bg_color)
        return send_file(result, mimetype='image/jpeg', download_name='detail_page.jpg')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
