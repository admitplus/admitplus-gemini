# AdmitPlus Backend

Backend for the AdmitPlus Multi-Agent Education OS — automating 50–70% of study-abroad agency workflows.


## 🚀 Features

- **Agency Management** - Create and manage educational agencies with member permission control
- **Student Profiles** - Student information management with invitation system
- **Application Management** - Complete application workflow with status tracking
- **Catalog Data** - Read-only master data for universities, programs, and checklist templates
- **User System** - Multi-role permissions with agency associations
- **Document Management** - File upload/download with presigned URLs
- **Event Auditing** - Application timeline and operation logs

### AI Components
- **Essay generation**
- **Essay scoring**
- **Requirement parsing**
- **Program matching**

## 🛠 Tech Stack

- **FastAPI** - High-performance API framework
- **MongoDB** - Data storage
- **Redis** - Caching and session management
- **JWT** - Authentication
- **Google Cloud Storage** - File storage
- **OpenAI** - AI-powered essay generation

## 📋 Prerequisites

- Python 3.13
- MongoDB
- Redis
- Google Cloud Project with Storage API enabled
- OpenAI API Key

## ⚡ Quick Start

### 1. Clone and Install

```bash
  git clone <repository-url>
```

```bash
  cd admitplus-b2b-backend
```

```bash
  pip install -r requirements.txt
```

### 2. Environment Setup

```bash
  # Edit .env with your configuration
  cp .env.example .env
  # Install pre-commit hooks
  pre-commit install
```

### 3. Google Cloud Storage Setup

The service account key is already included in the repository. No additional setup required.

### 4. Start the Application

```bash
  uvicorn admitplus.main:server --reload --port 8001
```

### 5. Access API Documentation

Visit `http://localhost:8001/docs` for interactive API documentation.

## 🏗 Architecture

This project follows a layered architecture pattern for clean separation of concerns:

```
Router → Service → Repository → Database
  ↓        ↓         ↓
Schema   Schema   Custom
```

### Layer Structure

1. **Router Layer** (`app/routers/`)
   - API endpoints and HTTP request handling
   - Request validation and response formatting
   - Returns structured data using Pydantic schemas

2. **Schema Layer** (`app/schemas/`)
   - Data structure definitions and validation
   - Pydantic models for type safety
   - Request/response schemas

3. **Service Layer** (`app/services/`)
   - Business logic implementation
   - Core business rules and workflows
   - Component coordination

4. **Repository Layer** (`app/repositories/`)
   - Database interaction and data persistence
   - CRUD operations
   - Data access patterns

## 👥 Team Collaboration

### Getting Started

1. **Clone the repository** - The service account key is already included
2. **Copy environment template**: `cp .env.example .env`
3. **Edit `.env`** with your local settings
4. **Install and run**: `pip install -r requirements.txt && uvicorn admitplus.main:server --reload --port 8001`

### Project Structure

```
admitplus-b2b-backend/
├── admitplus/                        # Application code
│   ├── app/                          # Core configuration
│       └── auth/
│       └── agency/
│       └── student/
│   ├── common/
│   ├── utils/
│   ├── llm/
│   └── dependencies/
├── config/
│   └── credentials/                  # Service account keys
│       └── admitplus-gcs-key.json
├── .env                              # Environment variables (not in Git)
├── .env.example                      # Environment template
├── .gitignore                        # Excludes sensitive files
└── README.md
```

## 🔒 Security

### Important Security Notes

- **Use secure channels** for key distribution
- **Rotate keys regularly** (every 90 days)
- **Use different keys** for different environments
- **Monitor key usage** and access logs

## 🚨 Troubleshooting

### Common Issues

#### Google Cloud Storage Authentication Error
```
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found
```

**Solution:**
1. Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to valid key file
2. Verify key file has correct permissions (600)
3. Check that service account has Storage Object Admin role

#### Missing Dependencies
```
ModuleNotFoundError: No module named 'bcrypt'
```

**Solution:**
```bash
  pip install -r requirements.txt
```

#### MongoDB Connection Error
```
pymongo.errors.ServerSelectionTimeoutError
```

**Solution:**
1. Ensure MongoDB is running
2. Check `MONGO_URI` in `.env` file
3. Verify MongoDB connection string format

### Verification Commands

```bash

# Test Google Cloud connection
python3 -c "from google.cloud import storage; storage.Client(); print('✅ GCS OK')"

# Test MongoDB connection
python3 -c "from motor.motor_asyncio import AsyncIOMotorClient; print('✅ MongoDB OK')"

# Test Redis connection
python3 -c "import redis; redis.Redis().ping(); print('✅ Redis OK')"
```

## 📚 API Documentation

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here]


## 📞 Support
#### support@admitplus.com

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above