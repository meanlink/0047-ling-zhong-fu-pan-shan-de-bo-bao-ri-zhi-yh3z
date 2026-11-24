import {options} from './ui.js'

export function pairForm(refs){
  return `<form id="pair"><label>日志号<input name="code" required pattern="[A-Z0-9-]{3,24}"></label>
   <label>基准源<select name="clock">${options(refs.filter(r=>r.enabled),r=>r.label)}</select></label>
   <label>基准铃点<input name="source_at" placeholder="2026-11-18T08:55:00+08:00" required></label>
   <label>实录铃点<input name="observed_at" placeholder="2026-11-18T08:55:00.180+08:00" required></label>
   <label>来源文件<input name="import_note" minlength="3" maxlength="255" required></label><button>配对登记</button><p role="status"></p></form>`
}
