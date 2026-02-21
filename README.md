# AI Knowledge Assistant - RAG System

## Project Structure
```
knowledge-assistant/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config.py
│   ├── models/
│   │   ├── user.py
│   │   ├── document.py
│   │   └── chat.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── chat.py
│   │   └── admin.py
│   ├── middleware/
│   │   └── auth_middleware.py
│   └── utils/
│       ├── embeddings.py
│       ├── rag.py
│       └── chunker.py
└── frontend/
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── index.js
        ├── App.js
        ├── index.css
        ├── context/
        │   ├── AuthContext.js
        │   └── ChatContext.js
        ├── services/
        │   └── api.js
        ├── components/
        │   ├── Navbar.js
        │   ├── ProtectedRoute.js
        │   └── LoadingSpinner.js
        └── pages/
            ├── Login.js
            ├── Register.js
            ├── Dashboard.js
            ├── Documents.js
            ├── Chat.js
            ├── ChatHistory.js
            └── AdminDashboard.js
```

## Setup Instructions

### Backend Setup
1. `cd backend`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in values
4. `python app.py`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm start`

### Environment Variables Required
- `MONGO_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT
- `OPENAI_API_KEY` - OpenAI API key (for embeddings + chat)
- `FLASK_ENV` - development or production