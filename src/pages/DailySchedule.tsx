import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { storage, ScheduleResponse } from '@/lib/storage';
import { motion, AnimatePresence } from 'motion/react';
import { Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

const MAX_RETRIES = 5;
const RETRY_DELAY = 1000; // 1 second

const DailySchedule = () => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Check for existing schedule on mount
  React.useEffect(() => {
    const existingSchedule = storage.getScheduleResponse();
    if (existingSchedule) {
      setSchedule(existingSchedule);
    }
  }, []);

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const handleGenerateSchedule = async () => {
    const userInputs = storage.getUserInputs();
    const sentimentResponse = storage.getSentimentResponse();

    if (!userInputs || !sentimentResponse) {
      toast({
        title: "Missing Required Data",
        description: "Please complete the mood analysis on the Home page first.",
        variant: "destructive"
      });
      return;
    }

    if (isLoading) {
      toast({
        title: "Processing",
        description: "Please wait while we generate your schedule.",
      });
      return;
    }

    setIsLoading(true);
    setRetryCount(0);

    try {
      // Prepare the data for API call
      const apiData = {
        user_thoughts: userInputs.user_thoughts.trim(),
        relationship: userInputs.relationship,
        cause_of_loss: userInputs.cause_of_loss
      };

      let data = null;
      let error = null;

      // Retry logic
      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        const result = await api.generateSchedule(apiData);
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
        storage.setScheduleResponse(data);
        setSchedule(data);
        toast({
          title: "Schedule Generated",
          description: "Your personalized daily schedule is ready."
        });
      }
    } catch (error) {
      console.error('Schedule generation failed:', error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Unable to generate schedule. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderTimeSlot = (title: string, activities: any[]) => (
    <Card className="mb-6 shadow-lg border-0 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
      <CardHeader>
        <CardTitle className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {activities.map((activity, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 rounded-lg bg-white/70 backdrop-blur-sm shadow-sm space-y-2 border border-purple-100 hover:shadow-md transition-all duration-300"
          >
            <h4 className="font-medium text-black">{activity.time_frame}</h4>
            <h3 className="text-lg font-semibold text-black">{activity.activity}</h3>
            <p className="text-gray-700">{activity.description}</p>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Your Daily Schedule</h1>
          <p className="text-gray-600 mb-6">
            A personalized daily schedule to help you navigate through your grief journey.
          </p>
          <Button
            onClick={handleGenerateSchedule}
            className="w-full max-w-md bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating{retryCount > 0 ? ` (Attempt ${retryCount + 1}/${MAX_RETRIES})` : '...'}
              </>
            ) : (
              'Generate Daily Schedule'
            )}
          </Button>
        </div>

        <AnimatePresence>
          {schedule && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {renderTimeSlot('Morning', schedule.morning)}
              {renderTimeSlot('Noon', schedule.noon)}
              {renderTimeSlot('Afternoon', schedule.afternoon)}
              {renderTimeSlot('Evening', schedule.evening)}
              {renderTimeSlot('Night', schedule.night)}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default DailySchedule;