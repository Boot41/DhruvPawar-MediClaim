# 🏥 MediClaim AI - Intelligent Insurance Claim Processing System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9+-blue.svg)](https://www.typescriptlang.org/)

An end-to-end AI-powered web application that revolutionizes insurance claim processing through intelligent document analysis, automated form generation, and interactive chatbot assistance. Built with modern technologies including FastAPI, React, and Google's AI Development Kit.

## 🌟 Key Features

### 📄 **Intelligent Document Processing**
- **Multi-format Support**: Process PDFs, scanned images, and text documents
- **Advanced OCR**: Extract text from scanned documents using Tesseract OCR
- **Smart Chunking**: Intelligent document segmentation for better AI processing
- **Document Analysis**: Extract structured data from policy documents and medical invoices

### 🤖 **AI-Powered Chatbot Assistant**
- **Interactive Support**: Real-time chat interface for insurance-related questions
- **Coverage Analysis**: Detailed explanations of insurance coverage and benefits
- **Document Queries**: Ask specific questions about uploaded documents
- **Terminology Help**: Get explanations of complex insurance terms and concepts

### 📊 **Automated Coverage Analysis**
- **Real-time Calculations**: Instant coverage calculations based on policy terms
- **Cost Breakdown**: Detailed analysis of deductibles, copays, and out-of-pocket costs

### 📝 **Smart Claim Form Generation**
- **AI-Generated Forms**: Automatically populate claim forms from document data
- **Form Preview**: Review and edit generated forms before submission
- **Missing Field Detection**: Identify and highlight incomplete information
- **One-Click Submission**: Streamlined claim submission process

### 🔄 **Workflow Management**
- **Step-by-Step Guidance**: Guided process through the entire claim workflow
- **Progress Tracking**: Real-time status updates and progress indicators
- **Session Management**: Persistent user sessions across browser sessions
- **State Management**: Comprehensive state tracking for complex workflows


## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Google API Key** for AI services
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/medclaim-ai.git
cd medclaim-ai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd medclaim-ai/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env_example.txt .env
# Edit .env with your Google API key and other settings

# Initialize database
python -c "from database_connection import init_database; init_database()"

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd medclaim-ai/frontend

# Install dependencies
npm install

# Set up environment variables
cp env.example .env.local
# Edit .env.local with your API URL

# Start the development server
npm start
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Technology Stack

### Backend Technologies
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and Object-Relational Mapping (ORM)
- **Google ADK** - AI Development Kit for intelligent agents
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server for running FastAPI applications

### Frontend Technologies
- **React 19** - Modern JavaScript library for building user interfaces
- **TypeScript** - Typed superset of JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Material-UI** - React components implementing Material Design
- **Axios** - Promise-based HTTP client

### AI & Machine Learning
- **Google Generative AI** - Advanced language models
- **Tesseract OCR** - Optical Character Recognition
- **PyMuPDF** - PDF processing and manipulation
- **LangChain** - Framework for developing applications with LLMs

### Database & Storage
- **SQLite** - Lightweight, serverless database
- **PostgreSQL** - Advanced open-source relational database (production)
- **File System** - Secure local file storage

## 📁 Project Structure

```
medclaim-ai/
├── backend/                    # FastAPI backend application
│   ├── apis/                   # API endpoints organized by category
│   │   ├── auth/              # Authentication endpoints
│   │   ├── document/          # Document management endpoints
│   │   ├── claim/             # Claim processing endpoints
│   │   └── chat/              # Chat assistant endpoints
│   ├── business_logic/         # Core business logic
│   │   ├── document/          # Document processing logic
│   │   ├── claim/             # Claim processing logic
│   │   └── agent/             # Agent orchestration logic
│   ├── agents/                # AI agents and tools
│   │   ├── tools/             # Agent tools and utilities
│   │   ├── instructions/      # Agent instructions and prompts
│   │   └── agents.py          # Agent definitions
│   ├── utils/                 # Utility functions and helpers
│   ├── config/                # Configuration and settings
│   ├── tests/                 # Comprehensive test suite
│   ├── templates/             # PDF templates
│   ├── uploads/               # File upload storage
│   ├── main.py                # FastAPI application entry point
│   ├── database.py            # Database models and schemas
│   ├── schemas.py             # Pydantic schemas for API validation
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React frontend application
│   ├── public/                # Static assets
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── contexts/          # React context providers
│   │   ├── services/          # API service functions
│   │   ├── App.tsx            # Main application component
│   │   └── index.tsx          # Application entry point
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind CSS configuration
├── processed/                  # Processed document outputs
├── sample_docs/               # Sample documents for testing
├── product/                   # Product documentation
│   ├── architecture.md        # System architecture documentation
│   ├── technical_spec.md      # Technical specifications
│   └── tasks.md               # Development tasks and roadmap
├── deliverables/              # Project deliverables
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PROJECT_ID=your_project_id_here

# Security
SECRET_KEY=your_secret_key_here

# Database
DATABASE_URL=sqlite:///./medclaim.db

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Frontend (.env.local)
```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Feature Flags
REACT_APP_ENABLE_CHAT=true
REACT_APP_ENABLE_ANALYTICS=false
```

## 📊 Database Schema

The system uses a comprehensive database schema with the following key entities:

- **Users** - User accounts and authentication
- **Insurance Policies** - User insurance policy information
- **Claims** - Insurance claim records and status
- **Documents** - Uploaded files and metadata
- **Chat Messages** - Conversation history with AI assistant
- **Workflow States** - User progress tracking
- **Processing Jobs** - Background task management

For detailed schema information, see [Architecture Documentation](product/architecture.md).

## 🚀 Deployment

### Development Deployment

Use the provided startup scripts:

```bash
# Backend
chmod +x start_backend.sh
./start_backend.sh

# Frontend
chmod +x start_frontend.sh
./start_frontend.sh
```

### Production Deployment

#### Backend (Docker)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend (Build)
```bash
cd frontend
npm run build
# Serve the build directory with nginx or similar
```

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

## 📈 Performance & Monitoring

### Key Metrics
- **Document Processing Time**: < 30 seconds for 20-page documents
- **API Response Time**: < 200ms for standard requests
- **Chat Response Time**: < 2 seconds for AI responses
- **Form Generation Time**: < 5 seconds for complex forms

### Monitoring Tools
- **Application Logs**: Comprehensive logging system
- **Error Tracking**: Automatic error detection and reporting
- **Performance Metrics**: Real-time performance monitoring
- **User Analytics**: Usage patterns and optimization insights

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **File Upload Validation**: Comprehensive file type and size validation
- **SQL Injection Prevention**: Parameterized queries and ORM protection
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Input Sanitization**: All user inputs are sanitized and validated
- **Secure File Storage**: Encrypted file storage with access controls

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features
- Update documentation as needed
- Follow conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Documentation

### Getting Help
- **Issues**: [GitHub Issues](https://github.com/yourusername/medclaim-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/medclaim-ai/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/medclaim-ai/wiki)

### Additional Resources
- [API Documentation](http://localhost:8000/docs) - Interactive API documentation
- [Architecture Guide](product/architecture.md) - Detailed system architecture
- [Technical Specifications](product/technical_spec.md) - Technical implementation details
- [Use Cases](Use%20Cases) - Business use cases and requirements

## 🗺️ Roadmap

### Phase 1: Core Features ✅
- [x] Document upload and processing
- [x] AI-powered chatbot assistant
- [x] Coverage analysis and calculation
- [x] Claim form generation
- [x] User authentication and session management

### Phase 2: Advanced Features 🚧
- [ ] Multi-language support
- [ ] Advanced fraud detection
- [ ] Integration with insurance APIs
- [ ] Mobile application
- [ ] Advanced analytics dashboard

### Phase 3: Enterprise Features 📋
- [ ] Multi-tenant architecture
- [ ] Advanced reporting and analytics
- [ ] Workflow automation
- [ ] Third-party integrations
- [ ] Compliance and audit features

## 🙏 Acknowledgments

- **Google AI** for providing the AI Development Kit
- **FastAPI** team for the excellent web framework
- **React** team for the powerful frontend library
- **Open Source Community** for the amazing tools and libraries

## 📞 Contact

- **Project Maintainer**: [Your Name](mailto:your.email@example.com)
- **Project Link**: [https://github.com/yourusername/medclaim-ai](https://github.com/yourusername/medclaim-ai)
- **Documentation**: [https://github.com/yourusername/medclaim-ai/wiki](https://github.com/yourusername/medclaim-ai/wiki)

---

<div align="center">

**MediClaim AI** - Making insurance claim processing simple, intelligent, and efficient! 🏥🤖

[⭐ Star this repo](https://github.com/yourusername/medclaim-ai) | [🐛 Report Bug](https://github.com/yourusername/medclaim-ai/issues) | [💡 Request Feature](https://github.com/yourusername/medclaim-ai/issues)

</div>
