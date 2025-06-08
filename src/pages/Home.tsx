import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { storage, UserInputs } from '@/lib/storage';
import { motion, AnimatePresence } from 'motion/react';
import { Loader2 } from 'lucide-react';
import Hero from '@/components/ui/hero';

const MOOD_EMOJIS = {
  Happy: '😊',
  Sad: '😢',
  Angry: '😡',
  Numb: '😐',
  Confused: '😕'
} as const;

const RELATIONSHIP_OPTIONS = [
'Parent', 'Child', 'Sibling', 'Partner', 'Friend', 'Other'];

const CAUSE_OPTIONS = [
'Illness', 'Accident', 'Suicide', 'Natural', 'Murder', 'Other'];

const MAX_RETRIES = 5;
const RETRY_DELAY = 1000; // 1 second

const Home = () => {
  const [formData, setFormData] = useState<UserInputs>({
    user_thoughts: '',
    relationship: '',
    cause_of_loss: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [currentMood, setCurrentMood] = useState<string | null>(null);
  const [showMoodDisplay, setShowMoodDisplay] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Load existing sentiment response on component mount
  React.useEffect(() => {
    const sentimentResponse = storage.getSentimentResponse();
    if (sentimentResponse) {
      setCurrentMood(sentimentResponse.mood);
      setShowMoodDisplay(true);
    }

    const userInputs = storage.getUserInputs();
    if (userInputs) {
      setFormData(userInputs);
    }
  }, []);

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.user_thoughts.trim() || !formData.relationship || !formData.cause_of_loss) {
      toast({
        title: "Please fill in all fields",
        description: "All fields are required to provide personalized support.",
        variant: "destructive"
      });
      return;
    }

    if (isLoading) {
      toast({
        title: "Processing",
        description: "Please wait while we analyze your input.",
      });
      return;
    }

    setIsLoading(true);
    setRetryCount(0);

    try {
      // Store user inputs first to ensure they're available for the API call
      storage.setUserInputs(formData);

      // Prepare the data for API call, ensuring all fields are properly formatted
      const apiData = {
        user_thoughts: formData.user_thoughts.trim(),
        relationship: formData.relationship,
        cause_of_loss: formData.cause_of_loss
      };

      let data = null;
      let error = null;

      // Retry logic
      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        const result = await api.analyzeSentiment(apiData);
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
        // Store sentiment response
        storage.setSentimentResponse(data);
        setCurrentMood(data.mood);
        setShowMoodDisplay(true);

        toast({
          title: "Analysis Complete",
          description: "Your emotional state has been analyzed. You can now explore grief support tools."
        });
      }
    } catch (error) {
      console.error('Sentiment analysis failed:', error);
      toast({
        title: "Analysis Failed",
        description: error instanceof Error ? error.message : "Unable to analyze your input. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const MoodEmoji = ({ mood, isActive }: {mood: keyof typeof MOOD_EMOJIS;isActive: boolean;}) => (
    <div className="relative flex items-center justify-center w-16 h-16 flex-shrink-0"> {/* Fixed container */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0.5 }}
        animate={{
          scale: isActive ? 1.1 : 0.8,
          opacity: isActive ? 1 : 0.3,
          filter: isActive ? 'grayscale(0%)' : 'grayscale(100%)'
        }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        className={`absolute text-5xl cursor-pointer transition-all duration-500 ${
          isActive ? 'drop-shadow-lg' : ''
        }`}
        whileHover={{ scale: isActive ? 1.2 : 0.9 }}
      >
        {MOOD_EMOJIS[mood]}
      </motion.div>
    </div>
  );

  return (
    <div className="bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <Hero />
      
      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 pb-8" id="grief-form">
        <div className="grid gap-8 md:grid-cols-2">
          {/* Form Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-2xl font-semibold text-gray-800">
                  Share Your Feelings
                  {retryCount > 0 && (
                    <span className="text-sm font-normal text-gray-500 ml-2">
                      (Attempt {retryCount + 1}/{MAX_RETRIES})
                    </span>
                  )}
                </CardTitle>
                <CardDescription>
                  Help us understand your current emotional state to provide personalized support.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="thoughts" className="text-sm font-medium">
                      How are you feeling today?
                    </Label>
                    <Textarea
                      id="thoughts"
                      placeholder="Share your thoughts and feelings..."
                      value={formData.user_thoughts}
                      onChange={(e) => setFormData((prev) => ({ ...prev, user_thoughts: e.target.value }))}
                      className="min-h-[120px] resize-none"
                      disabled={isLoading}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="relationship" className="text-sm font-medium">
                      Relationship with Deceased
                    </Label>
                    <Select
                      value={formData.relationship}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, relationship: value }))}
                      disabled={isLoading}>

                      <SelectTrigger>
                        <SelectValue placeholder="Select relationship" />
                      </SelectTrigger>
                      <SelectContent>
                        {RELATIONSHIP_OPTIONS.map((option) =>
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cause" className="text-sm font-medium">
                      Cause of Death
                    </Label>
                    <Select
                      value={formData.cause_of_loss}
                      onValueChange={(value) => setFormData((prev) => ({ ...prev, cause_of_loss: value }))}
                      disabled={isLoading}>

                      <SelectTrigger>
                        <SelectValue placeholder="Select cause" />
                      </SelectTrigger>
                      <SelectContent>
                        {CAUSE_OPTIONS.map((option) =>
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium py-3"
                    disabled={isLoading}>

                    {isLoading ?
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </> :

                    'Analyze My Feelings'
                    }
                  </Button>
                </form>
              </CardContent>
            </Card>
          </motion.div>

          {/* Mood Display Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm h-full">
              <CardHeader>
                <CardTitle className="text-2xl font-semibold text-gray-800">
                  Your Current Mood
                </CardTitle>
                <CardDescription>
                  Understanding your emotional state is the first step in your healing journey.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center py-8">
                <AnimatePresence mode="wait">
                  {showMoodDisplay ?
                  <motion.div
                    key="mood-display"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="text-center space-y-6 w-full">

                      <div className="flex justify-center gap-2 flex-wrap px-2">
                        {Object.keys(MOOD_EMOJIS).map((mood) =>
                      <MoodEmoji
                        key={mood}
                        mood={mood as keyof typeof MOOD_EMOJIS}
                        isActive={mood === currentMood} />

                      )}
                      </div>
                      
                      {currentMood &&
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 }}
                      className="text-center">

                          <p className="text-lg font-medium text-gray-700">
                            You're feeling: <span className="text-purple-600 font-semibold">{currentMood}</span>
                          </p>
                          <p className="text-sm text-gray-500 mt-2">
                            This is completely normal and valid. We're here to support you.
                          </p>
                        </motion.div>
                    }
                    </motion.div> :

                  <motion.div
                    key="placeholder"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center space-y-4">

                      <div className="flex justify-center gap-4 opacity-30">
                        {Object.values(MOOD_EMOJIS).map((emoji, index) =>
                      <div key={index} className="text-4xl">{emoji}</div>
                      )}
                      </div>
                      <p className="text-gray-500">
                        Share your feelings to see your current mood analysis
                      </p>
                    </motion.div>
                  }
                </AnimatePresence>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Next Steps */}
        {showMoodDisplay &&
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-8 text-center">

            <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <CardContent className="pt-6">
                <p className="text-gray-700 mb-4">
                  Ready for the next step? Explore personalized grief support tools based on your mood analysis.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button
                  onClick={() => window.location.href = '/grief-guide'}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white">
                    Explore Grief Guide
                  </Button>
                  <Button
                  onClick={() => window.location.href = '/daily-schedule'}
                  variant="outline"
                  className="border-purple-200 text-purple-700 hover:bg-purple-50">
                    Create Daily Schedule
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        }
      </div>
    </div>);

};

export default Home;