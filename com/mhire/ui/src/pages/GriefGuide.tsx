import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { storage, PersonalizedContentResponse } from '@/lib/storage';
import { motion, AnimatePresence } from 'motion/react';
import { Loader2, ExternalLink } from 'lucide-react';
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';

const MAX_RETRIES = 5;
const RETRY_DELAY = 1000; // 1 second

const GriefGuide = () => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [personalizedContent, setPersonalizedContent] = useState<PersonalizedContentResponse | null>(null);
  const [showMissingDataAlert, setShowMissingDataAlert] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    // Check if required data exists
    const userInputs = storage.getUserInputs();
    const sentimentResponse = storage.getSentimentResponse();
    const existingPersonalizedContent = storage.getPersonalizedContentResponse();
    const lastSelectedTool = storage.getSelectedTool();
  
    if (!userInputs || !sentimentResponse) {
      setShowMissingDataAlert(true);
    }

    if (existingPersonalizedContent) {
      setPersonalizedContent(existingPersonalizedContent);
    }

    if (lastSelectedTool) {
      setSelectedTool(lastSelectedTool);
    }
  }, []);

  // Function to extract YouTube video ID from URL
  const getYouTubeVideoId = (url: string) => {
    if (!url) return null;
    
    let videoId = '';
    if (url.includes('youtube.com/watch?v=')) {
      videoId = url.split('v=')[1].split('&')[0];
    } else if (url.includes('youtu.be/')) {
      videoId = url.split('youtu.be/')[1].split('?')[0];
    }
    return videoId;
  };

  // Function to create YouTube embed URL
  const getYouTubeEmbedUrl = (url: string) => {
    const videoId = getYouTubeVideoId(url);
    if (!videoId) return null;
    
    return `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&controls=1`;
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const handleToolSelect = async (
    toolTitle: string,
    toolDescription: string,
    toolName: string
  ) => {
    if (isLoading) {
      toast({
        title: "Processing",
        description: "Please wait while we generate your personalized content.",
      });
      return;
    }

    const userInputs = storage.getUserInputs();
    if (!userInputs) {
      setShowMissingDataAlert(true);
      return;
    }

    setIsLoading(true);
    setRetryCount(0);
    setSelectedTool(toolName);
    storage.setSelectedTool(toolName);

    try {
      // Convert tool title to match backend enum
      const titleMap: { [key: string]: string } = {
        "1. Stay Connected": "Stay connected",
        "2. Work Through Emotions": "Work Through Emotions",
        "3. Find Strength": "Find Strength",
        "4. Mindfulness": "Mindfulness",
        "5. Check In": "Check In",
        "6. Get Moving": "Get Moving"
      };
      
      const mappedToolTitle = titleMap[toolTitle];
      if (!mappedToolTitle) {
        throw new Error(`Invalid tool title: ${toolTitle}`);
      }

      const apiData = {
        ...userInputs,
        tool_title: mappedToolTitle,
        tool_description: toolDescription,
        tool_name: toolName
      };

      let data = null;
      let error = null;

      // Retry logic
      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        const result = await api.getPersonalizedContent(apiData);
        if (result.data) {
          data = result.data;
          break;
        } else if (attempt < MAX_RETRIES - 1) {
          await sleep(RETRY_DELAY * Math.pow(2, attempt)); // Exponential backoff
          setRetryCount(prev => prev + 1);
          continue;
        } else {
          error = result.error;
        }
      }

      if (error) {
        throw new Error(error);
      }

      if (data) {
        // Store personalized content in session storage
        storage.setPersonalizedContentResponse(data);
        setPersonalizedContent(data);
        toast({
          title: "Content Generated",
          description: "Your personalized grief support content is ready."
        });
      }
    } catch (error) {
      console.error('Content generation failed:', error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Unable to generate content. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderToolCards = () => {
    const sentimentResponse = storage.getSentimentResponse();
    if (!sentimentResponse) return null;

    return Object.entries(sentimentResponse.titles).map(([title, info]) => (
      <Card
        key={title}
        className="shadow-lg border-0 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200 transition-all duration-300 hover:shadow-xl"
      >
        <CardHeader>
          <CardTitle className="text-xl font-semibold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">{title}</CardTitle>
          <CardDescription>{info.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {info.tools.map((tool) => (
              <Button
                key={tool}
                className="w-full justify-start bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                disabled={isLoading}
                onClick={() => handleToolSelect(title, info.description, tool)}
              >
                {isLoading && selectedTool === tool ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating{retryCount > 0 ? ` (${retryCount + 1}/${MAX_RETRIES})` : '...'}
                  </>
                ) : (
                  tool
                )}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    ));
  };
  
  const renderPersonalizedContent = () => {
    if (!personalizedContent) return null;

    const embedUrl = getYouTubeEmbedUrl(personalizedContent.song_recommendation?.url);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        {/* Motivation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {personalizedContent.motivation_cards.map((card, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="group"
            >
              <Card className="relative overflow-hidden bg-gradient-to-br from-white via-purple-50/30 to-blue-50/50 border-0 shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 h-full">
                {/* Decorative background elements */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-200/40 to-transparent rounded-full transform translate-x-16 -translate-y-16 group-hover:scale-110 transition-transform duration-500"></div>
                <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-blue-200/40 to-transparent rounded-full transform -translate-x-12 translate-y-12 group-hover:scale-110 transition-transform duration-500"></div>
                
                {/* Card number badge */}
                <div className="absolute top-4 left-4 w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg">
                  {index + 1}
                </div>
                
                <CardContent className="relative p-8 pt-16 h-full flex flex-col justify-center">
                  {/* Quote marks decoration */}
                  <div className="absolute top-6 right-6 text-6xl text-purple-200/50 font-serif leading-none">"</div>
                  
                  <p className="text-gray-800 text-lg leading-relaxed font-medium relative z-10 text-center italic">
                    {card}
                  </p>
                  
                  {/* Bottom accent line */}
                  <div className="mt-6 w-16 h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full mx-auto opacity-60 group-hover:opacity-100 group-hover:w-24 transition-all duration-300"></div>
                </CardContent>
                
                {/* Subtle border glow effect */}
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-purple-400/20 to-blue-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Song Recommendation */}
        <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <CardHeader>
            <CardTitle className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">Song Recommendation</CardTitle>
          </CardHeader>
          <CardContent>
            <h3 className="font-semibold mb-2 text-gray-800">{personalizedContent.song_recommendation.title}</h3>
            <a 
              href={personalizedContent.song_recommendation.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="block aspect-video mb-4 rounded-lg overflow-hidden shadow-lg bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 transition-all duration-300 transform hover:scale-105 group"
            >
              <div className="w-full h-full flex flex-col items-center justify-center text-white">
                <div className="mb-4 p-6 bg-white/20 rounded-full backdrop-blur-sm group-hover:bg-white/30 transition-all duration-300">
                  <svg className="w-16 h-16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                </div>
                <h4 className="text-2xl font-bold mb-2 text-center px-4">{personalizedContent.song_recommendation.title}</h4>
                <p className="text-lg font-semibold bg-white/20 px-6 py-2 rounded-full backdrop-blur-sm group-hover:bg-white/30 transition-all duration-300">
                  Watch on YouTube
                </p>
              </div>
            </a>
            <p className="text-gray-600 mb-2">{personalizedContent.song_recommendation.reason}</p>
          </CardContent>
        </Card>

        {/* Essay */}
        <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <CardHeader>
            <CardTitle className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">Your Grief Journey</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-purple max-w-none">
            <blockquote className="text-lg font-medium italic mb-6 text-black border-l-4 border-purple-300 pl-4 bg-white/50 py-3 rounded-r">
              "{personalizedContent.essay.quote}"
            </blockquote>
            <div className="space-y-6">
              <div className="bg-white/50 p-4 rounded-lg">
                <h4 className="text-purple-600 font-semibold mb-2">Welcome to Grief Works</h4>
                <p className="text-gray-700">{personalizedContent.essay.welcome_to_grief_works}</p>
              </div>
              <div className="bg-white/50 p-4 rounded-lg">
                <h4 className="text-purple-600 font-semibold mb-2">Grief is Hard Work</h4>
                <p className="text-gray-700">{personalizedContent.essay.grief_is_hard_work}</p>
              </div>
              <div className="bg-white/50 p-4 rounded-lg">
                <h4 className="text-purple-600 font-semibold mb-2">About Your Grief</h4>
                <p className="text-gray-700">{personalizedContent.essay.about_your_grief}</p>
              </div>
              <div className="bg-white/50 p-4 rounded-lg">
                <h4 className="text-purple-600 font-semibold mb-2">Healing and Growing</h4>
                <p className="text-gray-700">{personalizedContent.essay.heal_and_grow}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8 px-4">
      <AlertDialog open={showMissingDataAlert}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Missing Required Data</AlertDialogTitle>
            <AlertDialogDescription>
              Please complete the mood analysis on the Home page first to access personalized grief support tools.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex justify-end">
            <Button
              onClick={() => window.location.href = '/'}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
            >
              Go to Home Page
            </Button>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Grief Support Tools</h1>
          <p className="text-gray-600">
            Select a tool below to receive personalized guidance and support for your grief journey.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {renderToolCards()}
        </div>

        {personalizedContent && renderPersonalizedContent()}
      </div>
    </div>
  );
};

export default GriefGuide;