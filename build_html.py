# -*- coding: utf-8 -*-
"""读取 data.json + other_platforms.json，生成自包含统计网页"""
import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

# 加载外部平台数据
ext_items = []
ext_file = HERE / "other_platforms.json"
if ext_file.exists():
    ext_items = json.loads(ext_file.read_text(encoding="utf-8"))

# 加载 hljcg 采购公告 (黑龙江政府采购网 API)
hljcg_items = []
hljcg_file = HERE / "hljcg_budget.json"
if hljcg_file.exists():
    hljcg_data = json.loads(hljcg_file.read_text(encoding="utf-8"))
    hljcg_items = hljcg_data.get("items", [])

# 加载采购人→客户经理映射
mgr_map = {}
keys_sorted = []
map_file = HERE / "buyer_manager_map.json"
if map_file.exists():
    mgr_data = json.loads(map_file.read_text(encoding="utf-8"))
    mgr_map = mgr_data.get("exact", {})
    keys_sorted = mgr_data.get("keys_sorted", [])

def find_manager(buyer_name):
    b = (buyer_name or "").strip()
    if not b:
        return ""
    if b in mgr_map:
        return mgr_map[b]
    for key in keys_sorted:
        if b.startswith(key):
            return mgr_map[key]
    return ""

# 给每条公告打负责人标签 + 来源平台
for item in data.get("items", []):
    item["manager"] = find_manager(item.get("buyer", ""))
    if "source" not in item:
        item["source"] = "中国政府采购网"

for item in ext_items:
    item["manager"] = find_manager(item.get("buyer", ""))

for item in hljcg_items:
    item["manager"] = find_manager(item.get("buyer", ""))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>鸡西地区政府采购项目统计（2026年起）</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f0f4f8;color:#2d3748;padding:16px}
.container{max-width:1400px;margin:0 auto}
h1{font-size:22px;color:#1a365d;margin:12px 0 4px}
.sub{color:#718096;font-size:13px;margin-bottom:16px}
.subbar{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
#btnUpdate{padding:8px 18px;border:none;border-radius:8px;background:#2b6cb0;color:#fff;font-size:14px;cursor:pointer;white-space:nowrap;transition:background .2s}
#btnUpdate:hover{background:#1a4f8a}
#btnUpdate:disabled{background:#a0aec0;cursor:not-allowed}
#updStatus{font-size:13px;color:#718096}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.card{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.08);text-align:center}
.card .num{font-size:26px;font-weight:700;color:#2b6cb0}
.card .lbl{font-size:12px;color:#718096;margin-top:4px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.toolbar input,.toolbar select{padding:8px 10px;border:1px solid #cbd5e0;border-radius:8px;font-size:14px;background:#fff}
.toolbar input{flex:1;min-width:140px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}
th{background:#2b6cb0;color:#fff;padding:10px 8px;font-size:13px;text-align:left;white-space:nowrap}
td{padding:9px 8px;font-size:13px;border-bottom:1px solid #edf2f7;vertical-align:top}
tr:hover td{background:#ebf8ff}
td a{color:#2b6cb0;text-decoration:none}
td a:hover{text-decoration:underline}
.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;background:#e6fffa;color:#234e52;white-space:nowrap}
.tag-source{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;white-space:nowrap}
.tag-source.ccgp{background:#e6fffa;color:#234e52}
.tag-source.other{background:#fefcbf;color:#744210}
.tag-source.hljcg{background:#fff7ed;color:#9a3412}
.pager{display:flex;gap:6px;justify-content:center;align-items:center;margin:14px 0;flex-wrap:wrap}
.pager button{padding:6px 12px;border:1px solid #cbd5e0;background:#fff;border-radius:6px;cursor:pointer;font-size:13px}
.pager button.on{background:#2b6cb0;color:#fff;border-color:#2b6cb0}
.pager input[type=number]{width:52px;padding:5px 6px;border:1px solid #cbd5e0;border-radius:6px;font-size:13px;text-align:center;-moz-appearance:textfield}
.pager input[type=number]::-webkit-inner-spin-button,.pager input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}
.pager .go-btn{padding:4px 10px;border:1px solid #2b6cb0;background:#2b6cb0;color:#fff;border-radius:6px;cursor:pointer;font-size:12px}
.pager .go-btn:hover{background:#1a4f8a}
.footer{text-align:center;color:#a0aec0;font-size:12px;margin:16px 0}
.tag2{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;background:#ebf4ff;color:#2a4365;white-space:nowrap}
.mgr{color:#718096;white-space:nowrap}
.no-mgr{color:#cbd5e0;white-space:nowrap}
.budget{color:#e53e3e;font-weight:600;white-space:nowrap}
.no-budget{color:#cbd5e0;white-space:nowrap}
@media(max-width:860px){th:nth-child(7),td:nth-child(7){display:none}}
</style>
</head>
<body>
<div class="container">
<h1>🏛️ 鸡西地区政府采购项目统计</h1>
<div class="sub">覆盖：鸡西市本级·鸡冠区·恒山区·鸡东县·城子河区·梨树区·麻山区·密山市·虎林市 ｜ 数据来源：中国政府采购网 + 其他采购平台 ｜ 统计范围：__RANGE__ ｜ 最近更新：__UPDATED__（每日 08:30 自动更新）</div>
<div class="subbar"><button id="btnUpdate">🔄 手动更新</button><span id="updStatus" style="font-size:12px;color:#718096">（点击触发云端更新，约2-3分钟完成）</span></div>
<div class="cards" id="cards"></div>
<div class="toolbar">
<input id="kw" placeholder="🔍 搜索项目名称 / 采购人 / 代理机构...">
<select id="fsource"><option value="">全部来源平台</option></select>
<select id="fregion"><option value="">全部地区</option></select>
<select id="fcat"><option value="">全部项目类别</option></select>
<select id="ftype"><option value="">全部公告类型</option></select>
<select id="fmonth"><option value="">全部月份</option></select>
</div>
<table>
<thead><tr><th style="width:32%">项目名称</th><th>来源</th><th>地区</th><th>公告类型</th><th>发布时间</th><th>预算金额</th><th>采购人</th><th>负责人</th></tr></thead>
<tbody id="tbody"></tbody>
</table>
<div class="pager" id="pager"></div>
<div class="footer">点击项目名称可跳转至原始公告页面 ｜ 金额单位：万元（人民币） ｜ 负责人信息依据客户经理集团明细表匹配</div>
</div>
<script>
var DATA=__DATA__;
var items=DATA.items;var PAGE=50;var cur=1;var filtered=items;
function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var REGION_ORDER=['鸡西市本级','鸡冠区','恒山区','鸡东县','城子河区','梨树区','麻山区','密山市','虎林市','其他'];
var CAT_ORDER=['信息化软件','硬件','集成','维保','其他'];
function stats(){
 var byType={};items.forEach(function(i){var t=i.type||'其他';byType[t]=(byType[t]||0)+1});
 var byRegion={};items.forEach(function(i){var r=i.region||'其他';byRegion[r]=(byRegion[r]||0)+1});
 var bySource={};items.forEach(function(i){var s=i.source||'中国政府采购网';bySource[s]=(bySource[s]||0)+1});
 var html='<div class="card"><div class="num">'+items.length+'</div><div class="lbl">公告总数</div></div>';
 REGION_ORDER.forEach(function(r){if(byRegion[r])html+='<div class="card"><div class="num">'+byRegion[r]+'</div><div class="lbl">'+esc(r)+'</div></div>'});
 document.getElementById('cards').innerHTML=html;
 // source filter
 var sf=document.getElementById('fsource');
 Object.keys(bySource).sort().forEach(function(s){var o=document.createElement('option');o.value=s;o.textContent=s+' ('+bySource[s]+')';sf.appendChild(o)});
 var sr=document.getElementById('fregion');REGION_ORDER.forEach(function(r){if(byRegion[r]){var o=document.createElement('option');o.value=r;o.textContent=r+' ('+byRegion[r]+')';sr.appendChild(o)}});
 var order=Object.keys(byType).sort(function(a,b){return byType[b]-byType[a]});
 var st=document.getElementById('ftype');order.forEach(function(t){var o=document.createElement('option');o.value=t;o.textContent=t+' ('+byType[t]+')';st.appendChild(o)});
 var byCat={};items.forEach(function(i){var c=i.category||'其他';byCat[c]=(byCat[c]||0)+1});
 var sc=document.getElementById('fcat');CAT_ORDER.forEach(function(c){if(byCat[c]){var o=document.createElement('option');o.value=c;o.textContent=c+' ('+byCat[c]+')';sc.appendChild(o)}});
 var months={};items.forEach(function(i){var m=(i.time||'').slice(0,7);if(m)months[m]=(months[m]||0)+1});
 var sm=document.getElementById('fmonth');Object.keys(months).sort().reverse().forEach(function(m){var o=document.createElement('option');o.value=m;o.textContent=m.replace('.','年')+'月 ('+months[m]+')';sm.appendChild(o)});
}
function apply(){
 var kw=document.getElementById('kw').value.trim().toLowerCase();
 var fs=document.getElementById('fsource').value;
 var ft=document.getElementById('ftype').value;
 var fm=document.getElementById('fmonth').value;
 var fr=document.getElementById('fregion').value;
 var fc=document.getElementById('fcat').value;
 filtered=items.filter(function(i){
  if(fs&&(i.source||'中国政府采购网')!==fs)return false;
  if(fr&&(i.region||'其他')!==fr)return false;
  if(fc&&(i.category||'其他')!==fc)return false;
  if(ft&&(i.type||'其他')!==ft)return false;
  if(fm&&(i.time||'').slice(0,7)!==fm)return false;
  if(kw&&!((i.title||'')+(i.buyer||'')+(i.agency||'')+(i.addr||'')).toLowerCase().includes(kw))return false;
  return true});
 cur=1;render()}
function render(){
 var tb=document.getElementById('tbody');var s=(cur-1)*PAGE;
 tb.innerHTML=filtered.slice(s,s+PAGE).map(function(i){
  var addrTip=i.addr?(' title="'+esc(i.addr)+'"'):'';
  var mgr=i.manager||'';
  var mgrHtml=mgr?'<span class="mgr">'+esc(mgr)+'</span>':'<span class="no-mgr">-</span>';
  var budget=i.budget||'';
  var budgetHtml=budget?'<span class="budget">'+esc(budget)+'</span>':'<span class="no-budget">-</span>';
  var src=i.source||'中国政府采购网';
  var isCc=src==='中国政府采购网';
  var srcHtml='<span class="tag-source '+(isCc?'ccgp':'other')+'">'+esc(src)+'</span>';
  return '<tr><td><a href="'+esc(i.url)+'" target="_blank">'+esc(i.title)+'</a></td><td>'+srcHtml+'</td><td><span class="tag2"'+addrTip+'>'+esc(i.region||'其他')+'</span></td><td><span class="tag">'+esc(i.type||'其他')+'</span></td><td>'+esc((i.time||'').slice(0,10))+'</td><td>'+budgetHtml+'</td><td>'+esc(i.buyer)+'</td><td>'+mgrHtml+'</td></tr>'}).join('')||'<tr><td colspan="8" style="text-align:center;color:#a0aec0;padding:24px">没有匹配的项目</td></tr>';
 var pages=Math.ceil(filtered.length/PAGE)||1;var pg=document.getElementById('pager');var html='';
 for(var p=1;p<=pages;p++){if(pages>12&&p>3&&p<pages-2&&Math.abs(p-cur)>1){if(html.slice(-9)!=='<span>…</span>')html+='<span>…</span>';continue}
  html+='<button class="'+(p===cur?'on':'')+'" onclick="go('+p+')">'+p+'</button>'}
 pg.innerHTML='共 '+filtered.length+' 条　'+html+'　<span style="font-size:13px;color:#718096">跳至</span> <input type="number" id="jumpPage" min="1" max="'+pages+'" value="'+cur+'" onkeydown="if(event.key===\'Enter\')jumpTo()"> <button class="go-btn" onclick="jumpTo()">GO</button>'+(pages>1?'<span style="font-size:13px;color:#a0aec0"> / 共'+pages+'页</span>':'')}
function go(p){cur=Math.max(1,Math.min(p,Math.ceil(filtered.length/PAGE)||1));render();window.scrollTo(0,0)}
function jumpTo(){var p=parseInt(document.getElementById('jumpPage').value);if(p>=1&&p<=Math.ceil(filtered.length/PAGE))go(p);else document.getElementById('jumpPage').value=cur}
document.getElementById('btnUpdate').addEventListener('click',function(){
 var b=this,s=document.getElementById('updStatus');
 if(b.disabled)return;
 b.disabled=true;b.textContent='⏳ 提交中…';s.textContent='正在触发云端更新…';
 fetch('https://api.github.com/repos/rumengling123/jixi-caigou/actions/workflows/update.yml/dispatches',{
  method:'POST',
  headers:{'Accept':'application/vnd.github+json','Authorization':'token __PAGES_UPDATE_TOKEN__'},
  body:JSON.stringify({ref:'main'})
 }).then(function(r){
  if(r.status===204){
   var i=0;
   b.textContent='⏳ 更新中…';s.textContent='云端正在执行（约2-3分钟），完成后请刷新页面';var t=setInterval(function(){
    s.textContent='云端正在执行（约2-3分钟'+'.'.repeat(i%4)+'）';
    i++;
   },800);
   setTimeout(function(){clearInterval(t);s.textContent='✅ 更新完成！请刷新页面查看最新数据';
    b.disabled=false;b.textContent='🔄 手动更新'},180000);
  }else{
   b.disabled=false;b.textContent='🔄 手动更新';s.textContent='❌ 触发失败，请稍后重试';
  }
 }).catch(function(){
  b.disabled=false;b.textContent='🔄 手动更新';s.textContent='❌ 网络错误，请稍后重试';
 });
});
document.getElementById('kw').addEventListener('input',apply);
document.getElementById('fsource').addEventListener('change',apply);
document.getElementById('fregion').addEventListener('change',apply);
document.getElementById('fcat').addEventListener('change',apply);
document.getElementById('ftype').addEventListener('change',apply);
document.getElementById('fmonth').addEventListener('change',apply);
stats();render();
</script>
</body>
</html>"""

range_str = data["range"]
if isinstance(range_str, (list, tuple)):
    range_str = " ~ ".join(str(x) for x in range_str)

# 合并数据：ccgp + 外部平台 + hljcg
all_items = list(data.get("items", [])) + list(ext_items) + list(hljcg_items)
# 去重：ccgp/外部用 url，hljcg 用 contentId
uniq = {}
for it in all_items:
    key = it.get("contentId") or it.get("url", "")
    if key:
        uniq[key] = it
merged = sorted(uniq.values(), key=lambda x: x.get("time", ""), reverse=True)

# Calculate latest update time across all sources
from datetime import datetime as _dt
_ts = [data.get("updated_at", "")]
if 'hljcg_data' in dir() and isinstance(hljcg_data, dict) and hljcg_data.get("updated_at"):
    _ts.append(hljcg_data["updated_at"])
_latest = max(_ts, key=lambda t: t if t else "")

merged_data = {
    "updated_at": _latest,
    "range": data.get("range", range_str),
    "total": len(merged),
    "items": merged,
}

html = (TEMPLATE
        .replace("__RANGE__", range_str)
        .replace("__UPDATED__", _latest)
        .replace("__DATA__", json.dumps(merged_data, ensure_ascii=False)))

# 注入 GitHub token（从环境变量读取，不出现在源代码中）
import os as _os
pages_token = _os.environ.get('PAGES_UPDATE_TOKEN', '')
if pages_token:
    html = html.replace('__PAGES_UPDATE_TOKEN__', pages_token)

out = HERE / "鸡西市政府采购项目统计.html"
out.write_text(html, encoding="utf-8")
# Also write index.html for surge deployment
(HERE / "index.html").write_text(html, encoding="utf-8")
print("OK ->", out, len(html), "bytes")
print("Total items:", len(merged))
print("  ccgp:", len(data.get("items", [])))
print("  other platforms:", len(ext_items))
print("  hljcg:", len(hljcg_items))
