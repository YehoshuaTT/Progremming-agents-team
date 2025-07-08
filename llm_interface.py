# LLM Integration for Enhanced Orchestrator
# Configuration file for connecting to actual LLM services

import os
from typing import Dict, Any, Optional
import asyncio
import aiohttp
import json
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Override existing environment variables
    print("SUCCESS: Environment variables loaded from .env file")
except ImportError:
    print("WARNING: python-dotenv not found. Install with: pip install python-dotenv")
    print("Using system environment variables only")

# Debug configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
VERBOSE_OUTPUT = os.getenv('VERBOSE_OUTPUT', 'false').lower() == 'true'

def debug_print(message: str, level: str = "INFO"):
    """Print debug messages if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

def verbose_print(message: str):
    """Print verbose messages if VERBOSE_OUTPUT is enabled"""
    if VERBOSE_OUTPUT or DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] VERBOSE: {message}")

class LLMInterface:
    """Interface for connecting to various LLM providers"""
    
    def __init__(self):
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_api_base = "https://api.openai.com/v1"
        self.openai_model = "gpt-3.5-turbo"
        
        # Gemini configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_api_base = "https://generativelanguage.googleapis.com/v1beta"
        self.gemini_model = "gemini-1.5-flash"  # Updated to working model
        
        # General configuration
        self.max_tokens = 4000
        self.temperature = 0.7
        
        # Determine which provider to use
        if self.gemini_api_key:
            self.provider = "gemini"
            debug_print("Using Gemini API provider")
            verbose_print(f"Gemini API key: {self.gemini_api_key[:10]}...")
        elif self.openai_api_key:
            self.provider = "openai"
            debug_print("Using OpenAI API provider")
            verbose_print(f"OpenAI API key: {self.openai_api_key[:10]}...")
        else:
            # In testing/CI environments, allow creation but use mock behavior
            self.provider = "mock"
            debug_print("No API key found - using mock provider for testing")
            # Only raise error if this is not a testing environment
            if not os.getenv('PYTEST_CURRENT_TEST') and not os.getenv('CI'):
                print("ERROR: No valid API key found!")
                print("API KEY: Please set either GEMINI_API_KEY or OPENAI_API_KEY in your .env file")
                print("EXAMPLE: GEMINI_API_KEY=your_api_key_here")
                raise ValueError("No LLM API key configured. Cannot proceed without valid API access.")
            
        verbose_print(f"Provider selected: {self.provider}")
        verbose_print(f"Max tokens: {self.max_tokens}, Temperature: {self.temperature}")
        
    async def call_llm(self, agent_name: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Call the LLM API with proper formatting for the specific agent"""
        debug_print(f"Starting LLM call for agent: {agent_name}")
        verbose_print(f"Prompt length: {len(prompt)} characters")
        
        if self.provider == "mock":
            # Fallback to mock responses if no API key
            debug_print("Using mock response fallback")
            return await self._mock_llm_response(agent_name, prompt, context)
        
        try:
            debug_print(f"Calling {self.provider} API...")
            if self.provider == "gemini":
                return await self._call_gemini_api(agent_name, prompt, context)
            elif self.provider == "openai":
                return await self._call_openai_api(agent_name, prompt, context)
            else:
                # This should never happen now since we raise error if no API key
                raise ValueError("No valid LLM provider configured")
                
        except Exception as e:
            debug_print(f"LLM call failed: {str(e)}", "ERROR")
            print(f"CRITICAL ERROR: LLM API call failed!")
            print(f"ERROR DETAILS: {str(e)}")
            print(f"API KEY: Please check your API key and internet connection")
            
            # Don't fall back to mock - raise the error to alert user
            raise Exception(f"LLM API call failed: {str(e)}. Please check your API configuration.")
    
    async def _call_openai_api(self, agent_name: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Call OpenAI API"""
        debug_print(f"Preparing OpenAI API call for {agent_name}")
        
        # Prepare the messages based on agent type
        messages = self._prepare_messages(agent_name, prompt, context)
        verbose_print(f"Prepared {len(messages)} messages")
        
        # Make the API call
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.openai_model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            debug_print(f"Sending request to OpenAI API...")
            async with session.post(
                f"{self.openai_api_base}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                debug_print(f"OpenAI API responded with status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def _call_gemini_api(self, agent_name: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Call Gemini API"""
        debug_print(f"Preparing Gemini API call for {agent_name}")
        
        # Prepare the prompt for Gemini
        system_prompt = self._get_system_prompt(agent_name)
        context_str = ""
        if context:
            context_str = f"Context: {json.dumps(context, indent=2)}\n\n"
            verbose_print(f"Added context: {len(context_str)} characters")
        
        full_prompt = f"{system_prompt}\n\n{context_str}Task: {prompt}"
        verbose_print(f"Full prompt length: {len(full_prompt)} characters")
        
        # Make the API call
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens
                }
            }
            
            url = f"{self.gemini_api_base}/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            
            debug_print(f"Sending request to Gemini API...")
            async with session.post(url, headers=headers, json=payload) as response:
                debug_print(f"Gemini API responded with status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    if "candidates" in result and len(result["candidates"]) > 0:
                        content = result["candidates"][0]["content"]["parts"][0]["text"]
                        debug_print(f"Received response: {len(content)} characters")
                        return content
                    else:
                        raise Exception("No content returned from Gemini API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
    
    def _prepare_messages(self, agent_name: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> list:
        """Prepare messages with agent-specific system prompts (for OpenAI)"""
        system_prompt = self._get_system_prompt(agent_name)
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add context if provided
        if context:
            context_str = f"Context: {json.dumps(context, indent=2)}"
            messages.append({"role": "user", "content": context_str})
        
        # Add the main prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def has_real_api_key(self) -> bool:
        """Check if a real API key is available (not using mock provider)"""
        return self.provider != "mock"
    
    def _get_system_prompt(self, agent_name: str) -> str:
        """Get system prompt for specific agent"""
        system_prompts = {
            "Product_Analyst": """You are a Product Analyst AI agent specialized in analyzing requirements and creating detailed specifications.
            Your role is to:
            1. Analyze user requirements thoroughly
            2. Create detailed technical specifications
            3. Identify functional and non-functional requirements
            4. Provide clear API endpoint definitions
            5. Always end with a structured handoff packet in JSON format
            
            Always be precise, thorough, and structure your output professionally.""",
            
            "Architect": """You are a System Architect AI agent specialized in designing technical architecture.
            Your role is to:
            1. Design system architecture based on requirements
            2. Choose appropriate technologies and frameworks
            3. Design database schemas and data models
            4. Create deployment and infrastructure plans
            5. Always end with a structured handoff packet in JSON format
            
            Focus on scalability, maintainability, and best practices.""",
            
            "Coder": """You are a Software Developer AI agent specialized in implementing clean, efficient code.
            Your role is to:
            1. Implement code based on specifications and architecture
            2. Write clean, readable, and maintainable code
            3. Follow coding best practices and conventions
            4. Create proper error handling and validation
            5. Always end with a structured handoff packet in JSON format
            
            Write production-ready code with proper documentation.""",
            
            "Code_Reviewer": """You are a Code Reviewer AI agent specialized in code quality and security.
            Your role is to:
            1. Review code for quality, logic, and maintainability
            2. Identify potential bugs and security issues
            3. Suggest improvements and optimizations
            4. Ensure adherence to coding standards
            5. Always end with a structured handoff packet in JSON format
            
            Be thorough but constructive in your feedback.""",
            
            "QA_Guardian": """You are a QA Guardian AI agent specialized in testing and quality assurance.
            Your role is to:
            1. Create comprehensive test plans and test cases
            2. Implement automated tests (unit, integration, e2e)
            3. Validate functionality and performance
            4. Ensure quality standards are met
            5. Always end with a structured handoff packet in JSON format
            
            Focus on comprehensive coverage and quality validation.""",
            
            "DevOps_Specialist": """You are a DevOps Specialist AI agent specialized in deployment and infrastructure.
            Your role is to:
            1. Create deployment configurations and scripts
            2. Set up CI/CD pipelines
            3. Configure environments (staging, production)
            4. Handle containerization and orchestration
            5. Always end with a structured handoff packet in JSON format
            
            Ensure reliable, scalable, and secure deployments.""",
            
            "Security_Specialist": """You are a Security Specialist AI agent focused on application security.
            Your role is to:
            1. Analyze code and architecture for security vulnerabilities
            2. Implement security best practices
            3. Configure authentication and authorization
            4. Ensure data protection and privacy
            5. Always end with a structured handoff packet in JSON format
            
            Prioritize security without compromising functionality.""",
            
            "Technical_Writer": """You are a Technical Writer AI agent specialized in documentation.
            Your role is to:
            1. Create comprehensive documentation for code and systems
            2. Write clear API documentation and user guides
            3. Document deployment and usage instructions
            4. Ensure documentation is accessible and maintainable
            5. Always end with a structured handoff packet in JSON format
            
            Write clear, concise, and helpful documentation."""
        }
        
        return system_prompts.get(agent_name, "You are a helpful AI assistant.")
    
    async def _mock_llm_response(self, agent_name: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic mock responses when LLM API is not available"""
        # Simulate some processing time
        await asyncio.sleep(1)
        
        if agent_name == "Product_Analyst":
            return self._generate_product_analyst_response(prompt, context)
        elif agent_name == "Architect":
            return self._generate_architect_response(prompt, context)
        elif agent_name == "Coder":
            return self._generate_coder_response(prompt, context)
        elif agent_name == "Code_Reviewer":
            return self._generate_code_reviewer_response(prompt, context)
        elif agent_name == "QA_Guardian":
            return self._generate_qa_response(prompt, context)
        elif agent_name == "DevOps_Specialist":
            return self._generate_devops_response(prompt, context)
        elif agent_name == "Security_Specialist":
            return self._generate_security_response(prompt, context)
        elif agent_name == "Technical_Writer":
            return self._generate_documentation_response(prompt, context)
        else:
            return f"Task completed for {agent_name}: {prompt[:100]}..."
    
    def _generate_product_analyst_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Product Analyst response"""
        timestamp = datetime.now().isoformat()
        
        if "JWT authentication" in prompt.lower() or "auth" in prompt.lower():
            return f'''# Product Specification: JWT Authentication System

## Overview
This specification defines requirements for implementing a JWT (JSON Web Token) based authentication system with user registration and login functionality.

## Functional Requirements

### User Registration
- Users must be able to register with email and password
- Email validation and uniqueness checking required
- Password strength requirements (minimum 8 characters, special characters)
- Account activation via email verification

### User Login
- Users authenticate using email/password credentials
- System generates JWT token upon successful authentication
- Token includes user ID, roles, and expiration time
- Invalid credentials return appropriate error messages

### JWT Token Management
- Tokens expire after 24 hours (configurable)
- Refresh token mechanism for extending sessions
- Token revocation capability for logout
- Secure token storage recommendations for clients

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile (authenticated)

## Non-Functional Requirements
- All authentication endpoints must use HTTPS
- Passwords stored using bcrypt hashing
- Rate limiting on authentication endpoints
- Comprehensive audit logging
- Response time under 200ms for authentication

## Security Requirements
- JWT secrets stored securely (environment variables)
- Protection against brute force attacks
- Input validation and sanitization
- CORS configuration for web clients

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "SPEC-AUTH-001",
  "agent_name": "Product_Analyst",
  "status": "SUCCESS",
  "artifacts_produced": ["specification.md"],
  "next_step_suggestion": "ARCHITECTURE_NEEDED",
  "notes": "Comprehensive JWT authentication specification complete. Ready for system architecture design.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["requirements_analysis"],
  "blocking_issues": []
}}
```'''
        
        # Generic response for other requests
        return f'''# Product Analysis Complete

## Requirements Analysis
Based on the request: "{prompt}"

## Functional Requirements
- Core functionality identified and documented
- User experience requirements defined
- API endpoints specified
- Data requirements established

## Next Steps
Ready for architectural design phase.

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "ANALYSIS-001",
  "agent_name": "Product_Analyst", 
  "status": "SUCCESS",
  "artifacts_produced": ["requirements.md"],
  "next_step_suggestion": "ARCHITECTURE_NEEDED",
  "notes": "Requirements analysis complete.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["analysis"],
  "blocking_issues": []
}}
```'''

    def _generate_architect_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Architect response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# System Architecture Design

## Architecture Overview
The system will be implemented using a microservices architecture with the following components:

## Technology Stack
- **Backend**: Node.js with Express.js framework
- **Database**: PostgreSQL for user data, Redis for session management
- **Authentication**: JWT with refresh token strategy
- **API**: RESTful API with OpenAPI documentation
- **Security**: bcrypt for password hashing, helmet.js for security headers

## Database Design
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Design
- RESTful endpoints following OpenAPI 3.0 specification
- Consistent error response format
- Rate limiting middleware
- Request validation middleware

## Security Architecture
- JWT tokens with 15-minute expiration
- Refresh tokens with 7-day expiration
- Secure HTTP-only cookie storage for refresh tokens
- CORS configuration for allowed origins

## Deployment Architecture
- Containerized application (Docker)
- Load balancer (Nginx)
- Database connection pooling
- Environment-based configuration

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "ARCH-001",
  "agent_name": "Architect",
  "status": "SUCCESS", 
  "artifacts_produced": ["architecture.md", "database_schema.sql"],
  "next_step_suggestion": "IMPLEMENTATION_NEEDED",
  "notes": "System architecture complete. Database schema and API design ready for implementation.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["requirements", "design"],
  "blocking_issues": []
}}
```'''

    def _generate_coder_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Coder response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# Implementation Complete

## Code Implementation
Successfully implemented the core functionality with the following components:

### Authentication Routes (auth.js)
```javascript
const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const {{ body, validationResult }} = require('express-validator');
const User = require('../models/User');
const router = express.Router();

// User Registration
router.post('/register', [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({{ min: 8 }}),
  body('firstName').trim().isLength({{ min: 1 }}),
  body('lastName').trim().isLength({{ min: 1 }})
], async (req, res) => {{
  try {{
    const errors = validationResult(req);
    if (!errors.isEmpty()) {{
      return res.status(400).json({{ errors: errors.array() }});
    }}

    const {{ email, password, firstName, lastName }} = req.body;
    
    // Check if user exists
    const existingUser = await User.findOne({{ email }});
    if (existingUser) {{
      return res.status(409).json({{ message: 'User already exists' }});
    }}

    // Hash password
    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // Create user
    const user = await User.create({{
      email,
      passwordHash,
      firstName,
      lastName
    }});

    res.status(201).json({{
      message: 'User created successfully',
      userId: user.id
    }});

  }} catch (error) {{
    console.error('Registration error:', error);
    res.status(500).json({{ message: 'Internal server error' }});
  }}
}});

// User Login
router.post('/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').exists()
], async (req, res) => {{
  try {{
    const errors = validationResult(req);
    if (!errors.isEmpty()) {{
      return res.status(400).json({{ errors: errors.array() }});
    }}

    const {{ email, password }} = req.body;
    
    const user = await User.findOne({{ email }});
    if (!user) {{
      return res.status(401).json({{ message: 'Invalid credentials' }});
    }}

    const isValidPassword = await bcrypt.compare(password, user.passwordHash);
    if (!isValidPassword) {{
      return res.status(401).json({{ message: 'Invalid credentials' }});
    }}

    // Generate JWT
    const token = jwt.sign(
      {{ userId: user.id, email: user.email }},
      process.env.JWT_SECRET,
      {{ expiresIn: '24h' }}
    );

    res.json({{
      message: 'Login successful',
      token,
      user: {{
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName
      }}
    }});

  }} catch (error) {{
    console.error('Login error:', error);
    res.status(500).json({{ message: 'Internal server error' }});
  }}
}});

module.exports = router;
```

### User Model (User.js)
```javascript
const {{ DataTypes }} = require('sequelize');
const sequelize = require('../config/database');

const User = sequelize.define('User', {{
  id: {{
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true
  }},
  email: {{
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {{
      isEmail: true
    }}
  }},
  passwordHash: {{
    type: DataTypes.STRING,
    allowNull: false
  }},
  firstName: {{
    type: DataTypes.STRING,
    allowNull: false
  }},
  lastName: {{
    type: DataTypes.STRING,
    allowNull: false
  }},
  emailVerified: {{
    type: DataTypes.BOOLEAN,
    defaultValue: false
  }}
}}, {{
  tableName: 'users',
  timestamps: true
}});

module.exports = User;
```

## Files Created
- `/routes/auth.js` - Authentication routes
- `/models/User.js` - User data model
- `/middleware/auth.js` - JWT authentication middleware
- `/config/database.js` - Database configuration
- `package.json` - Dependencies and scripts

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "CODE-001",
  "agent_name": "Coder",
  "status": "SUCCESS",
  "artifacts_produced": ["auth.js", "User.js", "auth_middleware.js", "package.json"],
  "next_step_suggestion": "CODE_REVIEW",
  "notes": "JWT authentication system implemented with registration, login, and middleware. Ready for code review.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["architecture", "database_design"],
  "blocking_issues": []
}}
```'''

    def _generate_code_reviewer_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Code Reviewer response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# Code Review Complete

## Review Summary
Comprehensive code review completed. Overall code quality is good with some recommendations for improvement.

## Findings

### ✅ Strengths
- Proper input validation using express-validator
- Secure password hashing with bcrypt (salt rounds: 12)
- Appropriate error handling and status codes
- Clean separation of concerns
- Proper use of async/await

### ⚠️ Recommendations
- Add rate limiting to prevent brute force attacks
- Implement request logging for security monitoring
- Add email verification flow for new registrations
- Consider adding password strength requirements on frontend
- Add unit tests for authentication functions

### 🔒 Security Considerations
- JWT secret should be strong and stored securely
- Consider implementing refresh token rotation
- Add CORS configuration for production
- Implement session management for logout functionality

## Next Steps
Code is ready for testing phase with recommended security enhancements.

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "REVIEW-001",
  "agent_name": "Code_Reviewer",
  "status": "SUCCESS",
  "artifacts_produced": ["code_review_report.md"],
  "next_step_suggestion": "TESTING_NEEDED",
  "notes": "Code review complete. Security recommendations provided. Ready for testing.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["code_implementation"],
  "blocking_issues": []
}}
```'''

    def _generate_qa_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic QA response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# QA Testing Complete

## Test Suite Implementation
Comprehensive testing suite implemented and executed successfully.

## Test Results
- **Unit Tests**: 15/15 passing ✅
- **Integration Tests**: 8/8 passing ✅  
- **Security Tests**: 6/6 passing ✅
- **Performance Tests**: 4/4 passing ✅

## Test Coverage
- Overall: 94%
- Authentication routes: 98%
- User model: 92%
- Middleware: 89%

## Performance Metrics
- Registration endpoint: 145ms avg
- Login endpoint: 123ms avg
- Protected routes: 45ms avg

## Security Validation
- Password hashing verified
- JWT signature validation working
- Input sanitization effective
- Rate limiting functional

## Quality Assurance Passed ✅

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "QA-001",
  "agent_name": "QA_Guardian",
  "status": "SUCCESS",
  "artifacts_produced": ["test_suite.js", "test_results.json", "coverage_report.html"],
  "next_step_suggestion": "DEPLOY_TO_STAGING",
  "notes": "All tests passing. System ready for deployment to staging environment.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["code_review", "testing"],
  "blocking_issues": []
}}
```'''

    def _generate_devops_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic DevOps response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# DevOps Deployment Ready

## Deployment Configuration Complete
Successfully configured deployment pipeline and infrastructure.

## Infrastructure Setup
- Docker containerization complete
- Nginx load balancer configured
- PostgreSQL database setup
- Redis session store configured
- SSL certificates installed

## Environment Configuration
- Staging environment: staging.example.com
- Production environment: api.example.com
- Health check endpoints: /health
- Monitoring: Prometheus + Grafana

## CI/CD Pipeline
- GitHub Actions workflow configured
- Automated testing on pull requests
- Staging deployment on main branch
- Production deployment on release tags

## Security Configuration
- Environment variables secured
- Database credentials encrypted
- API rate limiting enabled
- CORS properly configured

## Deployment Status: READY ✅

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "DEPLOY-001", 
  "agent_name": "DevOps_Specialist",
  "status": "SUCCESS",
  "artifacts_produced": ["Dockerfile", "docker-compose.yml", "nginx.conf", ".github/workflows/deploy.yml"],
  "next_step_suggestion": "DOCUMENTATION_NEEDED",
  "notes": "Deployment infrastructure ready. System deployed to staging successfully.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["testing", "security_review"],
  "blocking_issues": []
}}
```'''

    def _generate_security_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Security response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# Security Analysis Complete

## Security Assessment
Comprehensive security review completed with high security score.

## Security Features Implemented
- Password hashing with bcrypt (12 rounds)
- JWT token authentication
- Input validation and sanitization
- Rate limiting on auth endpoints
- HTTPS enforcement
- CORS configuration

## Security Scan Results
- No critical vulnerabilities found
- No high-risk issues detected
- 2 medium-risk recommendations addressed
- All dependencies up to date

## Recommendations Implemented
- Added request rate limiting
- Implemented secure headers middleware
- Enhanced error message security
- Added audit logging

## Security Score: A+ ✅

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "SEC-001",
  "agent_name": "Security_Specialist", 
  "status": "SUCCESS",
  "artifacts_produced": ["security_report.md", "security_config.js"],
  "next_step_suggestion": "HUMAN_APPROVAL_NEEDED",
  "notes": "Security analysis complete. System meets security standards. Ready for production approval.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["code_review", "deployment"],
  "blocking_issues": []
}}
```'''

    def _generate_documentation_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate realistic Documentation response"""
        timestamp = datetime.now().isoformat()
        
        return f'''# Documentation Complete

## Documentation Suite Created
Comprehensive documentation package completed and ready for use.

## Documentation Includes
- API Reference Documentation
- Installation and Setup Guide  
- User Guide and Examples
- Developer Documentation
- Deployment Instructions
- Security Guidelines

## API Documentation
Complete OpenAPI 3.0 specification with:
- Endpoint descriptions
- Request/response schemas
- Authentication requirements
- Error codes and messages
- Example requests and responses

## User Guide
Step-by-step instructions for:
- System setup and configuration
- User registration and login
- Token management
- Troubleshooting common issues

## Developer Documentation
Technical details including:
- Architecture overview
- Database schema
- Code structure and organization
- Testing procedures
- Contributing guidelines

## Documentation Quality: Excellent ✅

HANDOFF_PACKET:
```json
{{
  "completed_task_id": "DOC-001",
  "agent_name": "Technical_Writer",
  "status": "SUCCESS", 
  "artifacts_produced": ["README.md", "API_DOCS.md", "USER_GUIDE.md", "SETUP.md"],
  "next_step_suggestion": "MERGE_APPROVED",
  "notes": "Complete documentation suite ready. System fully documented and ready for production use.",
  "timestamp": "{timestamp}",
  "dependencies_satisfied": ["implementation", "testing", "deployment"],
  "blocking_issues": []
}}
```'''


# Global LLM interface instance - lazy initialization for testing environments
llm_interface = None

def get_llm_interface():
    """Get or create the global LLM interface instance"""
    global llm_interface
    if llm_interface is None:
        llm_interface = LLMInterface()
    return llm_interface

# For backward compatibility, try to create the instance immediately
# but handle missing API keys gracefully for testing/CI environments
try:
    llm_interface = LLMInterface()
except ValueError as e:
    if "No LLM API key configured" in str(e):
        # In testing/CI environments without API keys, create a mock instance
        print("INFO: No API key found - using mock LLM interface for testing")
        llm_interface = None  # Will be created on demand with mock behavior
    else:
        raise
