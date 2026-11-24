import {mount} from '/base.js'
import {roster} from './roster.js'
import {pairs} from './pairs.js'
import {drift} from './drift.js'
import {release} from './release.js'
const views={roster,pairs,drift,release}
mount({title:'岭钟复盘 · 山地播报日志',kicker:'千径自然步道志愿站 / 定时铃点留档',
 pages:{roster:'巡测时线',pairs:'双源配对簿',drift:'昼夜漂移谱',release:'复盘签发'},
 render:(page,root,user)=>views[page](root,user)})
