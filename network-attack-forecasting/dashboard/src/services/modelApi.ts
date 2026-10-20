import { apiClient } from './api';
import { MitreResponse, ModelExplainResponse, ModelInfo, SystemStatusResponse } from '../types';

export const modelApi = {
  getModelInfo: async (): Promise<ModelInfo> => {
    const res = await apiClient.get('/api/model/info');
    return res.data;
  },

  getModelExplain: async (): Promise<ModelExplainResponse> => {
    const res = await apiClient.get('/api/model/explain');
    return res.data;
  },

  getMitreMapping: async (): Promise<MitreResponse> => {
    const res = await apiClient.get('/api/mitre');
    return res.data;
  },

  getSystemStatus: async (): Promise<SystemStatusResponse> => {
    const res = await apiClient.get('/api/system/status');
    return res.data;
  },
};
