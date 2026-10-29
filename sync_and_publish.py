import os
import sys
import io
import json
import re
import glob
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

repo_dir = r'C:\Users\tsai_\OneDrive\桌面\20261015_南投草屯\南投縣草屯鎮生活處方完整版'
parent_dir = r'C:\Users\tsai_\OneDrive\桌面\20261015_南投草屯'
downloads_dir = r'c:\download'

LAYER_DEFAULT_STYLE = {
    '社交': { 'color': '#FF5252', 'iconCode': '1603', 'glyph': '🤝' },
    '紓壓': { 'color': '#097138', 'iconCode': '1891', 'glyph': '🌿' },
    '營養': { 'color': '#F57C00', 'iconCode': '1577', 'glyph': '🍎' },
    '運動': { 'color': '#1A237E', 'iconCode': '1893', 'glyph': '🏃' },
    '睡眠': { 'color': '#795548', 'iconCode': '1602', 'glyph': '😴' },
    '藥物安全': { 'color': '#9C27B0', 'iconCode': '1684', 'glyph': '💊' }
}

def find_latest_kml():
    candidates = []
    for d in [repo_dir, parent_dir, downloads_dir]:
        candidates.extend(glob.glob(os.path.join(d, '*生活處方*.kml')))
    
    # filter out 0 size
    valid = [c for c in candidates if os.path.isfile(c) and os.path.getsize(c) > 1000]
    if not valid:
        return None
    # sort by mtime desc
    valid.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return valid[0]

def convert_kml_to_data(kml_path):
    with open(kml_path, 'r', encoding='utf-8') as f:
        xml_text = f.read()

    root = ET.fromstring(xml_text)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    items = []
    seen = set()
    categories = []
    idx = 1

    for folder in root.findall('.//kml:Folder', ns):
        fname_el = folder.find('kml:name', ns)
        category = fname_el.text.strip() if fname_el is not None and fname_el.text else '社交'
        if category not in categories:
            categories.append(category)
            
        def_style = LAYER_DEFAULT_STYLE.get(category, {'color': '#FF5252', 'iconCode': '1603', 'glyph': '🤝'})
        
        for pm in folder.findall('kml:Placemark', ns):
            name_el = pm.find('kml:name', ns)
            coord_el = pm.find('.//kml:coordinates', ns)
            style_el = pm.find('kml:styleUrl', ns)
            desc_el = pm.find('kml:description', ns)
            
            if name_el is None or coord_el is None or not name_el.text or not coord_el.text:
                continue
                
            name = name_el.text.strip()
            parts = coord_el.text.strip().split(',')
            if len(parts) < 2:
                continue
            lng = float(parts[0])
            lat = float(parts[1])
            
            key = f"{category}|{name}|{lat:.6f}|{lng:.6f}"
            if key in seen:
                continue
            seen.add(key)
            
            def_code = def_style['iconCode']
            def_col = def_style['color']
            styleUrl = style_el.text.strip() if style_el is not None and style_el.text else f"#icon-{def_code}-{def_col[1:]}-nodesc"
            m = re.search(r'icon-(\d+)-([0-9A-Fa-f]{6})', styleUrl)
            iconCode = m.group(1) if m else def_code
            color = ('#' + m.group(2).upper()) if m else def_col
            glyph = def_style['glyph']
            
            raw_desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ''
            imgs = []
            for img_m in re.finditer(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', raw_desc, re.I):
                imgs.append(img_m.group(1))
                
            gx_media = pm.find('.//kml:Data[@name="gx_media_links"]/kml:value', ns)
            if gx_media is not None and gx_media.text:
                for u in gx_media.text.strip().split():
                    if u and u not in imgs:
                        imgs.append(u)
                        
            clean_desc = re.sub(r'<img[^>]*>', '', raw_desc, flags=re.I)
            clean_desc = re.sub(r'<br\s*/?>', '\n', clean_desc, flags=re.I)
            clean_desc = re.sub(r'<[^>]+>', '', clean_desc).strip()
            
            items.append({
                'id': f'p{idx}',
                'category': category,
                'name': name,
                'lat': lat,
                'lng': lng,
                'styleUrl': styleUrl,
                'color': color,
                'iconCode': iconCode,
                'glyph': glyph,
                'description': clean_desc,
                'images': imgs
            })
            idx += 1

    ver_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_data = {
        "documentName": "南投縣草屯鎮生活處方群組資料",
        "version": f"ver_{ver_stamp}",
        "updatedAt": datetime.now().isoformat(),
        "generatedAt": datetime.now().strftime("%Y-%m-%d"),
        "totalCount": len(items),
        "categories": categories,
        "items": items
    }
    return out_data, xml_text, ver_stamp

def main():
    print("=" * 60)
    print("🚀 草屯鎮生活處方服務點資料 同步發布工具")
    print("=" * 60)

    latest_kml = find_latest_kml()
    if not latest_kml:
        print("❌ 找不到最新的 KML 資料檔！")
        return

    print(f"📄 找到最新資料來源：{latest_kml}")
    data, xml_text, ver_stamp = convert_kml_to_data(latest_kml)
    print(f"📦 共解析出 {data['totalCount']} 筆服務點")
    desc_cnt = sum(1 for x in data['items'] if x['description'])
    img_cnt = sum(1 for x in data['items'] if x['images'])
    print(f"📝 含補充說明：{desc_cnt} 筆")
    print(f"📷 含實景照片：{img_cnt} 筆")

    # Write kml-data.js
    js_content = "window.DEFAULT_KML_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    target_js = os.path.join(repo_dir, 'kml-data.js')
    with open(target_js, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"✅ 已更新：{target_js}")

    # Copy to target KML
    target_kml = os.path.join(repo_dir, '南投縣草屯鎮生活處方群組資料.kml')
    with open(target_kml, 'w', encoding='utf-8') as f:
        f.write(xml_text)
    print(f"✅ 已更新：{target_kml}")

    # Update html cache query string
    for hname in ['index.html', '南投縣草屯鎮生活處方完整版.html']:
        hpath = os.path.join(repo_dir, hname)
        if os.path.exists(hpath):
            with open(hpath, 'r', encoding='utf-8') as f:
                hcontent = f.read()
            hcontent = re.sub(
                r'kml-data\.js(?:\?v=[^\"]*)?',
                f'kml-data.js?v={ver_stamp}',
                hcontent
            )
            with open(hpath, 'w', encoding='utf-8') as f:
                f.write(hcontent)
            print(f"✅ 已更新版本號於：{hname}")

    print("\n🌐 正在將更新推送到 GitHub（iPad 將可即時同步更新）...")
    try:
        subprocess.run(['git', '-C', repo_dir, 'add', '-A'], check=True)
        subprocess.run(['git', '-C', repo_dir, 'commit', '-m', f"sync: update prescription points data {ver_stamp}"], check=True)
        subprocess.run(['git', '-C', repo_dir, 'push', 'origin', 'main'], check=True)
        print("🎉 推送成功！iPad 重新整理或點選「🔄 同步最新資料」即可看到最新說明與照片！")
    except Exception as e:
        print(f"⚠️ Git 操作提醒：{e}")

if __name__ == '__main__':
    main()
