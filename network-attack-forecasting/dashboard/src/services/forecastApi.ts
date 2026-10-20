import { apiClient } from './api';
import { ForecastResponse } from '../types';

export const forecastApi = {
  getForecast: async (horizonSteps: number = 5, scenario?: string): Promise<ForecastResponse> => {
    const res = await apiClient.post('/api/forecast', {
      horizon_steps: horizonSteps,
      scenario,
    });
    return res.data;
  },
};
