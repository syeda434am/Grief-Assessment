import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Heart, Shield, Users, Clock } from 'lucide-react';
import { motion } from 'motion/react';

const Hero = () => {
  const features = [
    {
      icon: Heart,
      title: 'Compassionate Support',
      description: 'AI-powered emotional analysis with human empathy'
    },
    {
      icon: Shield,
      title: 'Safe & Private',
      description: 'Your feelings and data are completely secure'
    },
    {
      icon: Users,
      title: 'Personalized Care',
      description: 'Tailored guidance based on your unique situation'
    },
    {
      icon: Clock,
      title: '24/7 Available',
      description: 'Support whenever you need it, day or night'
    }
  ];

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50 py-20">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex items-center justify-center gap-3 mb-6">
              <Heart className="h-12 w-12 text-purple-600" />
              <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Grief Compass
              </h1>
            </div>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Your personalized guide through the journey of grief and healing. 
              We provide compassionate, AI-powered support to help you navigate 
              this difficult time with structured care and understanding.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-4 text-lg font-medium"
                onClick={() => {
                  const formSection = document.getElementById('grief-form');
                  if (formSection) {
                    formSection.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
              >
                Start Your Journey
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-purple-300 text-purple-600 hover:bg-purple-50 px-8 py-4 text-lg"
                onClick={() => window.location.href = '/grief-guide'}
              >
                Learn More
              </Button>
            </div>
          </motion.div>

          {/* What We Offer Section */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="mb-16"
          >
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              What We Offer
            </h2>
            <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
              Grief Compass combines advanced emotional analysis with personalized support tools 
              to help you process your feelings and build healthy coping strategies.
            </p>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.7 + index * 0.1 }}
                >
                  <Card className="h-full bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
                    <CardContent className="p-6 text-center">
                      <div className="flex justify-center mb-4">
                        <div className="p-3 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full">
                          <Icon className="h-8 w-8 text-purple-600" />
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 text-sm">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Hero;