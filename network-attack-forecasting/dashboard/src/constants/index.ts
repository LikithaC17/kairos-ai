import {
  LayoutDashboard,
  Activity,
  ShieldAlert,
  TrendingUp,
  PlayCircle,
  Crosshair,
  Bell,
  Cpu,
  Server,
  Settings,
} from 'lucide-react';

export const NAV_ITEMS = [
  { path: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { path: '/traffic', label: 'Live Traffic', icon: Activity },
  { path: '/threats', label: 'Threat Detection', icon: ShieldAlert },
  { path: '/forecast', label: 'Attack Forecast', icon: TrendingUp },
  { path: '/simulation', label: 'Attack Simulation', icon: PlayCircle },
  { path: '/mitre', label: 'MITRE ATT&CK', icon: Crosshair },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/model', label: 'Model Insights', icon: Cpu },
  { path: '/status', label: 'System Status', icon: Server },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const POLLING_INTERVALS = [
  { label: '5s (Real-time)', value: 5000 },
  { label: '10s (Fast)', value: 10000 },
  { label: '30s (Normal)', value: 30000 },
  { label: '60s (Slow)', value: 60000 },
  { label: 'Manual Only', value: 0 },
];

export const KILL_CHAIN_STAGES = [
  { id: 'RECONNAISSANCE', name: 'Reconnaissance', description: 'Port scanning, host discovery', mitre: 'T1046' },
  { id: 'INITIAL_ACCESS', name: 'Initial Access', description: 'Credential brute-force, web exploitation', mitre: 'T1110' },
  { id: 'LATERAL_MOVEMENT', name: 'Lateral Movement', description: 'Internal SMB/RDP remote pivot', mitre: 'T1021' },
  { id: 'COMMAND_AND_CONTROL', name: 'Command & Control', description: 'Outbound beaconing over HTTPS/DNS', mitre: 'T1071' },
  { id: 'EXFILTRATION', name: 'Data Exfiltration', description: 'Asymmetric outbound file transfer', mitre: 'T1048' },
  { id: 'IMPACT', name: 'Impact / DoS', description: 'Resource exhaustion, SYN flooding', mitre: 'T1498' },
];
