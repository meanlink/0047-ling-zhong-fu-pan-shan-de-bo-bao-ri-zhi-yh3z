import {h,badge} from '/base.js'
import {labels,stamp} from './phrases.js'

export function logRow(row,reviewer){
  return `<tr><th scope="row">${h(row.code)}<small>${h(row.ref_label)}</small></th><td>${stamp(row.source_at)}</td>
    <td>${stamp(row.observed_at)}</td><td>${h(row.import_note)}</td>
    <td>${row.label?badge(labels[row.label],row.label)+'<small>'+h(row.note)+'</small>':badge('计入')}
    ${reviewer?`<details><summary>签注排除</summary><form data-pair="${h(row.code)}"><label>原因<select name="label">
      <option value="unstable">时间源不稳</option><option value="human">人工录时误差</option></select></label>
      <label>依据<input name="note" minlength="5" maxlength="240" required></label><button>签记</button><p role="status"></p></form></details>`:''}</td></tr>`
}
