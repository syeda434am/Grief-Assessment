import { UserInputs, SentimentResponse, ScheduleResponse, PersonalizedContentResponse } from './storage';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Generic API call function
const apiCall = async <T,>(endpoint: string, data: any): Promise<{data: T | null; error: string | null;}> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'API call failed');
    }

    return { data: result.data, error: null };
  } catch (error) {
    console.error(`API call to ${endpoint} failed:`, error);
    return {
      data: null,
      error: error instanceof Error ? error.message : 'An unexpected error occurred'
    };
  }
};

// API functions
export const api = {
  // Sentiment analysis
  analyzeSentiment: async (inputs: UserInputs) => {
    return apiCall<SentimentResponse>('/sentiment-analyze', inputs);
  },

  // Daily schedule generation
  generateSchedule: async (inputs: UserInputs) => {
    return apiCall<ScheduleResponse>('/daily-schedule', inputs);
  },

  // Personalized content
  getPersonalizedContent: async (inputs: UserInputs & {
    tool_title: string;
    tool_description: string;
    tool_name: string;
  }) => {
    return apiCall<PersonalizedContentResponse>('/personalized-content', inputs);
  }
};