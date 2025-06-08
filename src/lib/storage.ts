// Utility functions for sessionStorage management

export interface UserInputs {
  user_thoughts: string;
  relationship: string;
  cause_of_loss: string;
}

export interface SentimentResponse {
  mood: 'Happy' | 'Sad' | 'Angry' | 'Numb' | 'Confused';
  titles: Record<string, {
    description: string;
    tools: string[];
  }>;
}

export interface ScheduleActivity {
  time_frame: string;
  activity: string;
  description: string;
}

export interface ScheduleResponse {
  morning: ScheduleActivity[];
  noon: ScheduleActivity[];
  afternoon: ScheduleActivity[];
  evening: ScheduleActivity[];
  night: ScheduleActivity[];
}

export interface PersonalizedContentResponse {
  motivation_cards: string[];
  song_recommendation: {
    title: string;
    url: string;
    reason: string;
  };
  essay: {
    quote: string;
    welcome_to_grief_works: string;
    grief_is_hard_work: string;
    about_your_grief: string;
    heal_and_grow: string;
  };
}

// Storage keys
const STORAGE_KEYS = {
  USER_INPUTS: 'userInputs',
  SENTIMENT_RESPONSE: 'sentimentResponse',
  SCHEDULE_RESPONSE: 'scheduleResponse',
  PERSONALIZED_CONTENT_RESPONSE: 'personalizedContentResponse',
  SELECTED_TOOL: 'selectedTool'
} as const;

// Generic storage functions
const setStorageItem = <T,>(key: string, value: T): void => {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error setting storage item ${key}:`, error);
  }
};

const getStorageItem = <T,>(key: string): T | null => {
  try {
    const item = sessionStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error(`Error getting storage item ${key}:`, error);
    return null;
  }
};

// Specific storage functions
export const storage = {
  // User inputs
  setUserInputs: (inputs: UserInputs) => setStorageItem(STORAGE_KEYS.USER_INPUTS, inputs),
  getUserInputs: (): UserInputs | null => getStorageItem<UserInputs>(STORAGE_KEYS.USER_INPUTS),

  // Sentiment response
  setSentimentResponse: (response: SentimentResponse) => setStorageItem(STORAGE_KEYS.SENTIMENT_RESPONSE, response),
  getSentimentResponse: (): SentimentResponse | null => getStorageItem<SentimentResponse>(STORAGE_KEYS.SENTIMENT_RESPONSE),

  // Schedule response
  setScheduleResponse: (response: ScheduleResponse) => setStorageItem(STORAGE_KEYS.SCHEDULE_RESPONSE, response),
  getScheduleResponse: (): ScheduleResponse | null => getStorageItem<ScheduleResponse>(STORAGE_KEYS.SCHEDULE_RESPONSE),

  // Personalized content response
  setPersonalizedContentResponse: (response: PersonalizedContentResponse) => setStorageItem(STORAGE_KEYS.PERSONALIZED_CONTENT_RESPONSE, response),
  getPersonalizedContentResponse: (): PersonalizedContentResponse | null => getStorageItem<PersonalizedContentResponse>(STORAGE_KEYS.PERSONALIZED_CONTENT_RESPONSE),

  // Selected tool
  setSelectedTool: (tool: string) => setStorageItem(STORAGE_KEYS.SELECTED_TOOL, tool),
  getSelectedTool: (): string | null => getStorageItem<string>(STORAGE_KEYS.SELECTED_TOOL),

  // Clear all data
  clearAll: () => {
    Object.values(STORAGE_KEYS).forEach((key) => {
      sessionStorage.removeItem(key);
    });
  }
};