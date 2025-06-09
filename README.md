# Grief Compass 🎗️

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen.svg)](https://grief-compass.vercel.app)

Grief Compass is a comprehensive digital platform designed to provide personalized support and guidance for individuals navigating through grief. By combining AI with empathetic design, this platform offers tailored resources, daily schedules, and interactive tools to help users process their grief journey in a healthy and supported way.

![Grief Compass](com/mhire/ui/public/gc.png)

## 🌟 Key Features

- 🤝 **Personalized Grief Support** - AI-powered content customization based on individual circumstances
- 📅 **Daily Schedule Builder** - Structured daily activities to maintain routine and wellness
- 🗣️ **Interactive Grief Guide** - Conversational interface for immediate emotional support
- 📊 **Sentiment Analysis** - Track and understand emotional patterns over time
- 🎯 **Progress Tracking** - Monitor your grief journey with actionable insights

## 🛠️ Technology Stack

- 🚀 **FastAPI** – High-performance Python-based backend with async capabilities
- 🧠 **AI Integration** – Backend powered by advanced AI model (Meta Llama 3 70b)
- ⚡️ **Vite** - Lightning fast build tool
- 🔥 **React 18** - Latest React features
- 🧩 **TypeScript** - Type safety for better developer experience
- 🎨 **TailwindCSS** - Utility-first CSS framework
- 🧰 **ShadCN UI** - Accessible and customizable UI components
- 📱 **Responsive Design** - Mobile-first approach
- 🧭 **React Router** - Easy client-side routing
- 🔄 **React Query** - Data fetching and state management
- 🧪 **Form Handling** - React Hook Form with Zod validation

## 🚀 Getting Started

### Prerequisites

#### Frontend Requirements
- Node.js 18+ 
- npm, yarn, or pnpm

#### Backend Requirements
- Python 3.10+
- pip
- FastAPI

### Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/Grief-Compass.git
cd Grief-Compass
```

2. Install frontend dependencies:
```bash
npm install
# or
yarn
# or
pnpm install
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=your_model_name
TAVILY_API_KEY=your_tavily_api_key
VITE_API_BASE_URL=http://localhost:8000
```

5. Start the backend server:
```bash
uvicorn com.mhire.app.main:app --reload --port 8000
```

6. Start the frontend development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

7. Open your browser and visit `http://localhost:5173`

## 📁 Project Structure

```
grief-compass/
├── com/                 # Backend Python package
│   └── mhire/app/
│       ├── main.py     # FastAPI application entry
│       ├── common/     # Shared utilities
│       ├── config/     # Configuration management
│       └── services/   # Backend services
│           ├── personalized_content/
│           ├── schedule_builder/
│           └── sentiment_toolkit/
├── src/                # Frontend source code
│   ├── components/     # React components
│   │   └── ui/        # ShadCN UI components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions
│   ├── pages/         # Page components
│   ├── App.tsx        # Main React component
│   ├── index.css      # Global styles
│   └── main.tsx       # Frontend entry point
├── public/            # Static assets
├── nginx/             # Nginx configuration
├── requirements.txt   # Python dependencies
├── package.json       # Node.js dependencies
└── docker-compose.yml # Docker configuration
```

## 🔧 API Endpoints

### Personalized Content
- `POST /api/personalized-content` - Generate personalized grief support content

### Schedule Builder
- `POST /api/schedule` - Create a personalized daily schedule

### Sentiment Analysis
- `POST /api/sentiment` - Analyze text for emotional content

## 🚀 Deployment

The application is deployed on Vercel with the following configuration:
- Frontend: Vercel Edge Network
- Backend: Vercel Serverless Functions

### Environment Variables Required for Deployment
```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=your_model_name
TAVILY_API_KEY=your_tavily_api_key
VITE_API_BASE_URL=your_production_api_url
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
