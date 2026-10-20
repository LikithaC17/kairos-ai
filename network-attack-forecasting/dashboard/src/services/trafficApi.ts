import { apiClient } from './api';
import { TrafficRecord, TrafficStats } from '../types';

export const trafficApi = {
  getTraffic: async (limit: number = 50): Promise<TrafficRecord[]> => {
    const res = await apiClient.get('/api/traffic', { params: { limit } });
    return res.data.records || [];
  },

  getTrafficStats: async (window: string = '15m'): Promise<TrafficStats> => {
    const res = await apiClient.get('/api/traffic/stats', { params: { window } });
    return res.data;
  },
};
