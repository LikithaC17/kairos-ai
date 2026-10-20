import { apiClient } from './api';
import { Threat, Alert } from '../types';

export const threatApi = {
  getThreats: async (severity?: string, threatType?: string, limit: number = 50): Promise<Threat[]> => {
    const res = await apiClient.get('/api/threats', {
      params: { severity, threat_type: threatType, limit },
    });
    return res.data.threats || [];
  },

  getThreatDetail: async (id: string): Promise<Threat> => {
    const res = await apiClient.get(`/api/threats/${id}`);
    return res.data;
  },

  getAlerts: async (): Promise<Alert[]> => {
    const res = await apiClient.get('/api/alerts');
    return res.data.alerts || [];
  },
};
