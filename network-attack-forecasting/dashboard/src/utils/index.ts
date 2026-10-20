import { SecurityState, SeverityLevel } from '../types';

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatTime(isoString?: string): string {
  if (!isoString) return '--:--:--';
  const d = new Date(isoString);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function getStateBadge(state: SecurityState): { label: string; bg: string; text: string; border: string } {
  switch (state) {
    case 'NORMAL':
      return { label: 'NORMAL', bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-600/40' };
    case 'ELEVATED':
      return { label: 'ELEVATED', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-600/40' };
    case 'SUSPICIOUS':
      return { label: 'SUSPICIOUS', bg: 'bg-orange-950/60', text: 'text-orange-400', border: 'border-orange-600/40' };
    case 'ATTACK':
      return { label: 'ATTACK', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-600/40' };
    default:
      return { label: state, bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };
  }
}

export function getSeverityBadge(severity: SeverityLevel): { label: string; bg: string; text: string; border: string } {
  switch (severity) {
    case 'LOW':
      return { label: 'LOW', bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-600/40' };
    case 'MEDIUM':
      return { label: 'MEDIUM', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-600/40' };
    case 'HIGH':
      return { label: 'HIGH', bg: 'bg-orange-950/60', text: 'text-orange-400', border: 'border-orange-600/40' };
    case 'CRITICAL':
      return { label: 'CRITICAL', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-600/40' };
    default:
      return { label: severity, bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };
  }
}
