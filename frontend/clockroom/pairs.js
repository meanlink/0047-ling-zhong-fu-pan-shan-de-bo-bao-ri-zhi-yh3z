import {api,empty} from '/base.js'
import {action,endpoint,heading,init,picker} from './ui.js'
import {logRow} from './log-row.js'
import {pairForm} from './record-form.js'

export async function pairs(root,user,selected){
  const {rows,code}=await init(selected)
  if(!code){root.innerHTML=empty('先排定巡测日。');return}
  const [list,refs]=await Promise.all([api(endpoint+'/tours/'+code+'/pairs'),api(endpoint+'/sources')])
  root.innerHTML=heading('双源配对簿','对照同一播报铃点的基准和实录时间，记录文件与标准来源。')
    +`<div class="clock-layout"><div class="log-table"><table><thead><tr><th>配对号</th><th>基准</th><th>实录时间</th><th>底账</th><th>证据</th></tr></thead>
    <tbody>${list.map(row=>logRow(row,user.role==='reviewer')).join('')}</tbody></table>
    ${list.length?'':empty('此巡测日尚无配对日志。')}</div><aside>${picker(rows,code)}${user.role==='operator'?pairForm(refs):''}</aside></div>`
  root.querySelector('#tour').onchange=e=>pairs(root,user,e.target.value)
  action(root.querySelector('#pair'),data=>api(endpoint+'/tours/'+code+'/pairs','POST',data),()=>pairs(root,user,code))
  for(const form of root.querySelectorAll('[data-pair]'))
    action(form,data=>api(endpoint+'/pairs/'+form.dataset.pair+'/note','PUT',data),()=>pairs(root,user,code))
}
