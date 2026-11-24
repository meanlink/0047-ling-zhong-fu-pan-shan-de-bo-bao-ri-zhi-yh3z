import {h} from '/base.js'
import {stamp} from './phrases.js'

export function line(row){
  const start=new Date(row.start).getTime(),end=new Date(row.end).getTime(),cut=new Date(row.cut).getTime()
  const percent=100*(cut-start)/(end-start)
  return `<article class="clockline"><h2>${h(row.name)}<small>${h(row.code)} / ${h(row.tour_day)}</small></h2>
  <div class="scale"><span class="diurnal" style="flex:${percent}">日段</span><span class="nocturnal" style="flex:${100-percent}">夜段</span></div>
  <div class="axis"><time>${stamp(row.start)}</time><time>${stamp(row.cut)}</time><time>${stamp(row.end)}</time></div></article>`
}
