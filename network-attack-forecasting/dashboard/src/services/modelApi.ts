import { apiClient } from './api';
import { ActiveModelResponse, MitreResponse, ModelBenchmarkComparison, ModelExplainResponse, ModelInfo, SystemStatusResponse } from '../types';

export const modelApi = {
  getModelInfo: async (model?: string): Promise<ModelInfo> => {
    const params = model ? { model } : undefined;
    const res = await apiClient.get('/api/model/info', { params });
    return res.data;
  },

  getModelComparison: async (): Promise<ModelBenchmarkComparison> => {
    const res = await apiClient.get('/api/models/comparison');
    return res.data;
  },

  getActiveModel: async (): Promise<ActiveModelResponse> => {
    const res = await apiClient.get('/api/models/active');
    return res.data;
  },

  setActiveModel: async (model: string): Promise<{ status: string; active_model: string; message: string }> => {
    const res = await apiClient.post('/api/models/active', { model });
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
