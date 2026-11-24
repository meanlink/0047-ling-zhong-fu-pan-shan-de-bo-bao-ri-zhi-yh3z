import {api,h} from '/base.js'
import {endpoint,heading} from './ui.js'
import {line} from './clock-strip.js'

export async function roster(root){
  const [tours,refs]=await Promise.all([api(endpoint+'/tours'),api(endpoint+'/sources')])
  root.innerHTML=heading('巡测时线','山地步道播报亭按本地 06:00 开始一轮巡测，次日凌晨继续上一巡次。')
    +`<div class="clock-layout"><section>${tours.map(line).join('')}</section><aside><h2>时间源登记</h2>
      ${refs.map(ref=>`<p><strong>${h(ref.label)}</strong><br><small>${h(ref.code)} · ${ref.enabled?'可用':'停用'} · 标称 ${ref.uncertainty_ms} ms</small></p>`).join('')}</aside></div>`
}
