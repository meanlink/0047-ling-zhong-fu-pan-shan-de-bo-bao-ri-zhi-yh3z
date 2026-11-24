import {h} from '/base.js'
import {ms,segments} from './phrases.js'

export function deviation(name,row,axis){
  const drift=row.trend?.slope_ms_per_hour;
  const correlation=row.trend?.within_source_r;
  const relation=drift==null?'重复基准配对不足':drift+' ms/小时 · r '+(correlation??'—');
  return `<article class="deviation"><header><h2>${segments[name]}</h2><b>${h(ms(row.offset_ms))}</b></header>
   <div class="oscillator">${row.values.map((value,index)=>`<span title="${h(ms(value))}"
   style="left:${48+48*value/axis}%;top:${20+(index%4)*8}px"></span>`).join('')}</div><small>左侧提前 · 轴中零点 · 右侧延后</small>
   <p>基准源偏移差 ${ms(row.range_ms)} / 有效 ${row.count} 条</p>
   <p>源内时间与偏移相关性 · ${h(relation)}</p>
   <ul>${Object.entries(row.source_medians).map(([source,value])=>`<li>${h(source)} <b>${ms(value)}</b></li>`).join('')}</ul></article>`
}
