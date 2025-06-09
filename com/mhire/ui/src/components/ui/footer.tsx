import React from 'react';
import { Heart, Mail, Shield, Users } from 'lucide-react';
import { motion } from 'motion/react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = [
    {
      title: 'Resources',
      links: [
        { name: 'Grief Guide', href: '/grief-guide' },
        { name: 'Daily Schedule', href: '/daily-schedule' },
        { name: 'Community', href: '#' }
      ]
    }
  ];

  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="bg-gradient-to-r from-gray-900 via-purple-900 to-blue-900 text-white mt-20"
    >
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Brand Section */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <Heart className="h-8 w-8 text-purple-400" />
              <h3 className="text-2xl font-bold text-white">
                Grief Compass
              </h3>
            </div>
            <p className="text-gray-300 mb-4">
              Guiding you through your healing journey with personalized support and compassionate care.
            </p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Shield className="h-4 w-4" />
                <span>Secure & Private</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Users className="h-4 w-4" />
                <span>24/7 Support</span>
              </div>
            </div>
          </div>

          {/* Links Sections - Positioned at far right */}
          <div className="md:col-span-1 flex justify-end">
            <div>
              <h4 className="text-lg font-semibold mb-4 text-white">Resources</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/grief-guide"
                    className="text-gray-300 hover:text-purple-400 transition-colors duration-200 text-sm"
                  >
                    Grief Guide
                  </a>
                </li>
                <li>
                  <a
                    href="/daily-schedule"
                    className="text-gray-300 hover:text-purple-400 transition-colors duration-200 text-sm"
                  >
                    Daily Schedule
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-700 mt-8 pt-8">
          <div className="flex justify-center">
            <div className="text-gray-400 text-sm">
              © {currentYear} Grief Compass. All rights reserved. Made with compassion.
            </div>
          </div>
        </div>
      </div>
    </motion.footer>
  );
};

export default Footer;