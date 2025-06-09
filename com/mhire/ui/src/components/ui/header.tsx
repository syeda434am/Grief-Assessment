import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Home, Calendar, Heart } from 'lucide-react';
import { motion } from 'motion/react';

const Header = () => {
  const currentPath = window.location.pathname;

  const navItems = [
    {
      path: '/',
      label: 'Home',
      icon: Home
    },
    {
      path: '/daily-schedule',
      label: 'Daily Schedule',
      icon: Calendar
    },
    {
      path: '/grief-guide',
      label: 'Grief Guide',
      icon: Heart
    }
  ];

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full bg-white/90 backdrop-blur-sm shadow-sm border-b border-gray-100 sticky top-0 z-50"
    >
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Heart className="h-8 w-8 text-purple-600" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Grief Compass
            </h1>
          </div>

          {/* Navigation - Upper Right */}
          <nav className="flex items-center gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPath === item.path;
              
              return (
                <Button
                  key={item.path}
                  variant={isActive ? "default" : "ghost"}
                  size="sm"
                  onClick={() => window.location.href = item.path}
                  className={`flex items-center gap-2 px-4 py-2 transition-all duration-200 ${
                    isActive 
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md' 
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="font-medium">{item.label}</span>
                </Button>
              );
            })}
          </nav>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;