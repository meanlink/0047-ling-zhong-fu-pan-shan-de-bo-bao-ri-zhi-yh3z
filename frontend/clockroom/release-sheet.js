import {h,badge} from '/base.js'
import {ms,phase,segments} from './phrases.js'

export function docket(report,signed){
  return `<article class="docket"><header><h2>复盘校时意见</h2>${badge(phase[report.phase],report.phase)}</header>
   <dl>${Object.entries(report.segments).map(([key,row])=>`<div><dt>${segments[key]}建议偏移</dt>
   <dd>${h(ms(row.adjust_ms))}</dd></div>`).join('')}</dl>
   <p>签注保留排除项 ${h(report.excluded.join('、')||'无')}</p>
   ${signed?`<p>签发人 ${h(signed.editor)}</p>`:''}</article>`
}
