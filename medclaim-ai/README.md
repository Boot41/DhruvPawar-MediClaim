# MediClaim AI - Insurance Claim Processing System

An end-to-end web application for processing insurance claims using AI-powered document analysis, chatbot assistance, and automated form generation.

## 🚀 Features

### 1. **Document Upload & Processing**
- Upload large PDF documents (20-30 pages)
- Intelligent document chunking for better processing
- Support for policy documents, medical invoices, and medical records
- OCR and text extraction from images

### 2. **AI-Powered Chatbot**
- Interactive chat interface for insurance questions
- Coverage analysis and explanations
- Document-specific queries and analysis
- Insurance terminology explanations

### 3. **Coverage Analysis**
- Automatic calculation of insurance coverage
- Deductible and copay analysis
- Out-of-pocket cost estimation
- Visual coverage breakdown

### 4. **Claim Form Generation**
- AI-generated claim forms based on uploaded documents
- Form preview and editing capabilities
- Missing field identification
- One-click form submission

### 5. **Workflow Management**
- Step-by-step guided process
- Progress tracking
- Session management
- Real-time status updates

## 🏗️ Architecture

### Backend (FastAPI + Google ADK)
- **Document Processing**: Intelligent chunking and text extraction
- **AI Agents**: Google ADK-powered specialized agents
- **Database**: SQLite/PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based user authentication
- **File Handling**: Secure file upload and processing

### Frontend (React + TypeScript)
- **Modern UI**: Tailwind CSS with responsive design
- **State Management**: React Context for global state
- **Routing**: React Router for navigation
- **Components**: Modular, reusable components

### AI Agents
- **Document Analyzer**: Extracts structured data from documents
- **Coverage Analyzer**: Calculates insurance coverage
- **Chat Assistant**: Handles user questions and support
- **Claim Form Generator**: Creates personalized claim forms

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google API Key
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd medclaim-ai
```

### 2. Backend Setup
```bash
# Make scripts executable
chmod +x start_backend.sh

# Start backend server
./start_backend.sh
```

Or manually:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY="your_google_api_key_here"
export SECRET_KEY="your_secret_key_here"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Make scripts executable
chmod +x start_frontend.sh

# Start frontend server
./start_frontend.sh
```

Or manually:
```bash
cd frontend
npm install
export REACT_APP_API_URL="http://localhost:8000"
npm start
```

### 4. Environment Configuration

Create `backend/.env`:
```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PROJECT_ID=your_project_id_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///./medclaim.db
```

Create `frontend/.env.local`:
```env
REACT_APP_API_URL=http://localhost:8000
```

## 🎯 Usage

### 1. **User Registration/Login**
- Register a new account or login with existing credentials
- Secure JWT-based authentication

### 2. **Document Upload**
- Upload insurance policy documents
- Upload medical invoices and bills
- Upload supporting medical records
- Documents are automatically processed and chunked

### 3. **Chat with AI Assistant**
- Ask questions about your coverage
- Get explanations of insurance terms
- Query specific information from your documents
- Get guidance on the claim process

### 4. **Coverage Analysis**
- View detailed coverage breakdown
- See what your insurance will cover
- Understand out-of-pocket costs
- Print coverage reports

### 5. **Claim Form Generation**
- Generate personalized claim forms
- Review and edit form data
- Fill in missing information
- Submit claims directly

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/session` - Create session

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - Get user documents

### Chat
- `POST /api/chat` - Send chat message
- `GET /api/chat/history/{session_id}` - Get chat history

### Coverage
- `POST /api/coverage/calculate` - Calculate coverage

### Claims
- `POST /api/claims/generate-form` - Generate claim form
- `POST /api/claims/submit` - Submit claim

### Workflow
- `GET /api/workflow/{session_id}` - Get workflow state
- `POST /api/workflow/{session_id}/update` - Update workflow state

## 🧠 AI Agents

### Document Analyzer Agent
- Extracts structured data from policy and invoice documents
- Identifies key information like policy numbers, coverage amounts, deductibles
- Processes document chunks for better accuracy

### Coverage Analyzer Agent
- Calculates insurance coverage based on policy and invoice data
- Explains coverage terms and conditions
- Provides detailed cost breakdowns

### Chat Assistant Agent
- Handles general insurance questions
- Provides explanations of complex terms
- Guides users through the claim process

### Claim Form Generator Agent
- Creates personalized claim forms
- Maps document data to form fields
- Identifies missing information

## 📊 Database Schema

### Core Tables
- **Users**: User accounts and authentication
- **UserSessions**: Active user sessions
- **Documents**: Uploaded files and metadata
- **DocumentChunks**: Processed document chunks
- **ChatMessages**: Chat conversation history
- **Claims**: Claim records and status
- **WorkflowStates**: User progress tracking

## 🔒 Security Features

- JWT-based authentication
- File upload validation
- SQL injection prevention
- CORS configuration
- Input sanitization
- Secure file storage

## 🚀 Deployment

### Backend Deployment
1. Set up production database (PostgreSQL recommended)
2. Configure environment variables
3. Use production WSGI server (Gunicorn)
4. Set up reverse proxy (Nginx)

### Frontend Deployment
1. Build production bundle: `npm run build`
2. Serve static files with web server
3. Configure API URL for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API endpoints

## 🔄 Updates

### Recent Updates
- ✅ Complete end-to-end application setup
- ✅ Google ADK agent integration
- ✅ Document chunking system
- ✅ React frontend with modern UI
- ✅ Comprehensive API endpoints
- ✅ Authentication and session management
- ✅ Real-time chat interface
- ✅ Coverage analysis and calculation
- ✅ Claim form generation and preview

---

**MediClaim AI** - Making insurance claim processing simple and intelligent! 🏥🤖
