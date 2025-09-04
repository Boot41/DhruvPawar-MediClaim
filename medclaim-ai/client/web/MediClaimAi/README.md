# MediClaim AI - Frontend

A modern, production-ready React frontend for the MediClaim AI insurance claim processing system. Built with React, Tailwind CSS, and integrated with Google ADK Web backend.

## Features

- 🤖 **Intelligent Chat Interface** - Conversational UI for insurance claim processing
- 📄 **Document Upload** - Drag & drop support for policy documents and medical bills
- 📊 **Coverage Analysis** - Real-time calculation and visualization of insurance coverage
- 🏢 **Vendor Selection** - Interactive insurance provider selection
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile
- ⚡ **Real-time Updates** - Live progress tracking and status updates
- 🎨 **Modern UI** - Clean, professional interface with smooth animations

## Tech Stack

- **React 19** - Latest React with concurrent features
- **Tailwind CSS 4** - Utility-first CSS framework
- **Framer Motion** - Smooth animations and transitions
- **Lucide React** - Beautiful, customizable icons
- **React Router** - Client-side routing
- **Vite** - Fast build tool and dev server

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Google ADK Web backend running

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update environment variables in `.env`:
```env
VITE_API_BASE_URL=http://localhost:8080
VITE_ADK_APP_NAME=health-insurance-agent
```

4. Start development server:
```bash
npm run dev
```

5. Open [http://localhost:5173](http://localhost:5173) in your browser

## Project Structure

```
src/
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── Button.jsx
│   │   ├── Input.jsx
│   │   ├── Card.jsx
│   │   ├── FileUpload.jsx
│   │   └── ...
│   ├── chat/              # Chat-specific components
│   │   ├── ChatContainer.jsx
│   │   ├── ChatMessage.jsx
│   │   ├── ChatInput.jsx
│   │   ├── ProgressSteps.jsx
│   │   ├── CoverageAnalysis.jsx
│   │   └── VendorSelection.jsx
│   └── ErrorBoundary.jsx
├── services/
│   └── api.js             # Google ADK Web API integration
├── App.jsx
└── main.jsx
```

## Integration with Google ADK Web

The frontend is designed to work seamlessly with your Google ADK Web backend:

- **Session Management** - Automatic session creation and management
- **Real-time Communication** - WebSocket-like communication through ADK Web
- **File Upload** - Secure file handling for policy documents and medical bills
- **State Synchronization** - Frontend state synced with backend conversation state

### API Endpoints

The app communicates with these ADK Web endpoints:

- `POST /apps/health-insurance-agent/users/user/sessions` - Start new session
- `POST /apps/health-insurance-agent/users/user/sessions/{id}/messages` - Send messages
- `GET /apps/health-insurance-agent/users/user/sessions/{id}` - Get session data

## Conversation Flow

1. **Welcome** - User starts conversation
2. **Policy Upload** - Upload insurance policy document
3. **Invoice Upload** - Upload medical bills/invoices
4. **Coverage Analysis** - AI calculates coverage and displays breakdown
5. **Vendor Selection** - Choose insurance provider
6. **Form Processing** - AI processes claim form
7. **Completion** - Download completed claim form

## Components Overview

### UI Components (`src/components/ui/`)

- **Button** - Versatile button with multiple variants and loading states
- **Input** - Form input with validation and error handling
- **Card** - Container component for content sections
- **FileUpload** - Drag & drop file upload with progress
- **ProgressBar** - Visual progress indicator
- **Alert** - Notification and error messages

### Chat Components (`src/components/chat/`)

- **ChatContainer** - Main chat interface with state management
- **ChatMessage** - Individual message display with formatting
- **ChatInput** - Message input with file upload support
- **ProgressSteps** - Visual step-by-step progress indicator
- **CoverageAnalysis** - Interactive coverage breakdown display
- **VendorSelection** - Insurance provider selection interface

## Deployment

### Production Build

```bash
npm run build
```

### Environment Variables

Set these environment variables for production:

```env
VITE_API_BASE_URL=https://your-adk-web-domain.com
VITE_ADK_APP_NAME=health-insurance-agent
NODE_ENV=production
```

### Deployment Options

- **Netlify** - Connect your GitHub repo for automatic deployments
- **Vercel** - Zero-config deployment with GitHub integration
- **AWS S3 + CloudFront** - Scalable static hosting
- **Google Cloud Storage** - Integrated with your ADK Web backend

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use Tailwind CSS for styling
- Implement proper error boundaries
- Add loading states for better UX

## Contributing

1. Follow the existing code structure
2. Add proper TypeScript types where needed
3. Test components thoroughly
4. Update documentation for new features
5. Ensure responsive design

## License

This project is part of the MediClaim AI system.
