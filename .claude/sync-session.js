#!/usr/bin/env node
/**
 * sync-session.js
 * Leggi all'INIZIO di ogni sessione: node .claude/sync-session.js [developer] [branch] [file1,file2,...]
 * Esempi:
 *   node .claude/sync-session.js davide feature/7-tactics src/tactics.py,src/behavior_engine.py
 *   node .claude/sync-session.js pedro feature/8-gem-grab src/game_modes/gem_grab.py,src/detector.py
 *
 * Se nessun argomento: solo mostra stato corrente senza modificare.
 */

const fs = require('fs');
const path = require('path');

const ACTIVE_FILE = path.join(__dirname, '.tasks', 'active.json');
const STALE_HOURS = 2;

function readActive() {
  try {
    return JSON.parse(fs.readFileSync(ACTIVE_FILE, 'utf8'));
  } catch {
    console.error('❌ Impossibile leggere .claude/.tasks/active.json');
    process.exit(1);
  }
}

function isStale(session) {
  if (!session.last_update) return true;
  const diff = (Date.now() - new Date(session.last_update).getTime()) / 3600000;
  return diff > STALE_HOURS;
}

function checkConflicts(mine, theirs, theirName) {
  const myFiles = [...(mine.files_owned || []), ...(mine.files_shared || [])];
  const theirFiles = [...(theirs.files_owned || []), ...(theirs.files_shared || [])];
  return theirFiles.filter(f => myFiles.includes(f));
}

const args = process.argv.slice(2);
const [developer, branch, filesArg] = args;

const active = readActive();

// — Mostra stato attuale ————————————————————————————
console.log('\n═══════════════════════════════════════');
console.log('  BRAWL-BOT SESSION SYNC');
console.log('═══════════════════════════════════════');

for (const dev of ['davide', 'pedro']) {
  const s = active[dev];
  if (!s) continue;
  const stale = s.status === 'active' && isStale(s);
  const statusIcon = s.status === 'active' && !stale ? '🟢' : s.status === 'active' && stale ? '🟡' : '⚪';
  const staleNote = stale ? ' (STALE - non aggiornato da >' + STALE_HOURS + 'h)' : '';
  console.log(`\n${statusIcon} ${dev.toUpperCase()}`);
  if (s.status === 'active' && !stale) {
    console.log(`   branch: ${s.branch}`);
    if (s.files_owned.length) console.log(`   owned:  ${s.files_owned.join(', ')}`);
    if (s.files_shared.length) console.log(`   shared: ${s.files_shared.join(', ')}`);
    console.log(`   da: ${s.start_time}`);
  } else {
    console.log(`   status: ${s.status}${staleNote}`);
  }
}

// — Se nessun argomento, solo mostra ———————————————
if (!developer) {
  console.log('\n═══════════════════════════════════════\n');
  process.exit(0);
}

// — Validazione ————————————————————————————————————
if (!['davide', 'pedro'].includes(developer)) {
  console.error(`\n❌ developer deve essere "davide" o "pedro", ricevuto: "${developer}"`);
  process.exit(1);
}

const myFiles = filesArg ? filesArg.split(',').map(f => f.trim()) : [];
const other = developer === 'davide' ? 'pedro' : 'davide';
const otherSession = active[other];

// — Controlla conflitti —————————————————————————————
const sharedFiles = ['src/capture.py','src/detector.py','src/controller.py','src/config.py','src/game_state.py','main.py'];
const myShared = myFiles.filter(f => sharedFiles.includes(f));
const myOwned = myFiles.filter(f => !sharedFiles.includes(f));

if (otherSession && otherSession.status === 'active' && !isStale(otherSession)) {
  const theirFiles = [...(otherSession.files_owned || []), ...(otherSession.files_shared || [])];
  const conflicts = myFiles.filter(f => theirFiles.includes(f));
  if (conflicts.length > 0) {
    console.log(`\n⚠️  CONFLITTO RILEVATO!`);
    console.log(`   ${other.toUpperCase()} sta già modificando: ${conflicts.join(', ')}`);
    console.log(`   branch di ${other}: ${otherSession.branch}`);
    console.log('\n   Opzioni:');
    console.log('   1. Rimuovi questi file dal tuo task e contatta su COLLAB.md');
    console.log('   2. Aspetta che Pedro/Davide finisca (controlla ogni 30min con: node .claude/sync-session.js)');
    console.log('   3. Crea issue su GitHub con label "shared-file"\n');
    process.exit(0);
  } else {
    console.log(`\n✅ Nessun conflitto con ${other} (${otherSession.branch})`);
  }
} else {
  console.log(`\n✅ ${other} non è in sessione attiva`);
}

// — Aggiorna active.json con sessione corrente ————————
active[developer] = {
  status: 'active',
  branch: branch || 'unknown',
  files_owned: myOwned,
  files_shared: myShared,
  start_time: new Date().toISOString(),
  last_update: new Date().toISOString(),
  pr_url: null
};

fs.writeFileSync(ACTIVE_FILE, JSON.stringify(active, null, 2));

console.log(`\n🚀 Sessione avviata: ${developer} su ${branch || 'unknown'}`);
if (myOwned.length) console.log(`   owned:  ${myOwned.join(', ')}`);
if (myShared.length) console.log(`   ⚠️  shared: ${myShared.join(', ')} (avvisa l'altro!)`);
console.log('\n═══════════════════════════════════════');
console.log('  Ricorda: git add .claude/.tasks/active.json && git push origin dev');
console.log('  Fine sessione: node .claude/update-active-session.js [developer]');
console.log('═══════════════════════════════════════\n');
