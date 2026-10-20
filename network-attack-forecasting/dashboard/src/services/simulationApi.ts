import { apiClient } from './api';
import { SimulationRunResult, SimulationScenario } from '../types';

export const simulationApi = {
  getScenarios: async (): Promise<SimulationScenario[]> => {
    const res = await apiClient.get('/api/simulation/scenarios');
    return res.data.scenarios || [];
  },

  runSimulation: async (scenario: string, steps: number = 20, speedMs: number = 1000): Promise<SimulationRunResult> => {
    const res = await apiClient.post('/api/simulation/run', {
      scenario,
      steps,
      speed_ms: speedMs,
    });
    return res.data;
  },
};
