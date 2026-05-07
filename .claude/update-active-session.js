#!/usr/bin/env node
/**
 * update-active-session.js
 * Chiudi la sessione a fine lavoro.
 * Uso: node .claude/update-active-session.js [developer] [pr_url?]
 * Esempi:
 *   node .claude/update-active-session.js davide
 *   node .claude/update-active-session.js pedro https://github.com/Pedronane/brawl-bot/pull/12
 */

const fs = require('fs');
const path = require('path');

const ACTIVE_FILE = path.join(__dirname, '.tasks', 'active.json');

const [developer, pr_url] = process.argv.slice(2);

if (!developer || !['davide', 'pedro'].includes(developer)) {
  console.error('Uso: node .claude/update-active-session.js [davide|pedro] [pr_url?]');
  process.exit(1);
}

let active;
try {
  active = JSON.parse(fs.readFileSync(ACTIVE_FILE, 'utf8'));
} catch {
  console.error('❌ Impossibile leggere .claude/.tasks/active.json');
  process.exit(1);
}

const session = active[developer];
if (!session || session.status !== 'active') {
  console.log(`⚪ ${developer}: nessuna sessione attiva da chiudere.`);
  process.exit(0);
}

const duration = session.start_time
  ? Math.round((Date.now() - new Date(session.start_time).getTime()) / 60000)
  : null;

active[developer] = {
  ...session,
  status: 'idle',
  last_update: new Date().toISOString(),
  pr_url: pr_url || session.pr_url || null,
};

fs.writeFileSync(ACTIVE_FILE, JSON.stringify(active, null, 2));

console.log(`\n✅ Sessione ${developer} chiusa.`);
if (duration !== null) console.log(`   Durata: ${duration} minuti`);
if (session.branch) console.log(`   Branch: ${session.branch}`);
if (pr_url) console.log(`   PR: ${pr_url}`);
console.log('\nProssimo step:');
console.log('  git add .claude/.tasks/active.json .claude/COLLAB.md');
console.log('  git commit -m "[collab] ' + developer + ': close session ' + (session.branch || '') + '"');
console.log('  git push origin dev\n');
