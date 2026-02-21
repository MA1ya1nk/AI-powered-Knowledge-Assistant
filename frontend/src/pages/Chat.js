// pages/Chat.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import Navbar from '../components/Navbar';
import { chatAPI } from '../services/api';
import { useChat } from '../context/ChatContext';
import toast from 'react-hot-toast';

function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
      overflow: 'hidden', fontSize: 13
    }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 8,
          padding: '8px 12px', background: 'var(--bg-3)',
          border: 'none', cursor: 'pointer', color: 'var(--text-1)',
          fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 600
        }}
      >
        <span style={{
          width: 20, height: 20, borderRadius: '50%',
          background: 'var(--accent)', color: 'white',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 800, flexShrink: 0
        }}>{index}</span>
        <span style={{ flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {source.document_name}
        </span>
        <span style={{ color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
          {(source.similarity_score * 100).toFixed(0)}%
        </span>
        <span style={{ color: 'var(--text-3)' }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{ padding: '10px 12px', background: 'var(--bg-2)', color: 'var(--text-2)', lineHeight: 1.6 }}>
          {source.excerpt}
        </div>
      )}
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 20, animation: 'fadeIn 0.25s ease'
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%', flexShrink: 0, marginRight: 12, marginTop: 4,
          background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
      )}
      
      <div style={{ maxWidth: '75%' }}>
        <div style={{
          padding: '12px 16px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          background: isUser ? 'var(--accent)' : 'var(--bg-2)',
          color: isUser ? 'white' : 'var(--text-0)',
          border: isUser ? 'none' : '1px solid var(--border)',
          lineHeight: 1.65,
          fontSize: 14
        }}>
          {isUser ? (
            <p style={{ margin: 0 }}>{msg.content}</p>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>
        
        {/* Sources */}
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
              Sources
            </div>
            {msg.sources.map((src, i) => (
              <SourceCard key={i} source={src} index={i + 1} />
            ))}
          </div>
        )}
        
        {msg.tokens_used > 0 && !isUser && (
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 6, fontFamily: 'var(--font-mono)' }}>
            {msg.tokens_used} tokens
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { currentSession, setCurrentSession, messages, setMessages } = useChat();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  // Load existing session
  useEffect(() => {
    if (sessionId && (!currentSession || currentSession.id !== sessionId)) {
      setLoadingSession(true);
      chatAPI.getSession(sessionId)
        .then(res => {
          setCurrentSession(res.data.session);
          setMessages(res.data.messages);
        })
        .catch(() => {
          toast.error('Session not found');
          navigate('/chat');
        })
        .finally(() => setLoadingSession(false));
    }
  }, [sessionId]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;
    
    setInput('');
    setLoading(true);

    // Optimistic user message
    const tempUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
      sources: [],
      tokens_used: 0
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const res = await chatAPI.ask({
        question,
        session_id: currentSession?.id || null
      });

      const { session_id, session_title, user_message, assistant_message } = res.data;

      // Update session
      if (!currentSession) {
        const newSession = { id: session_id, title: session_title };
        setCurrentSession(newSession);
        navigate(`/chat/${session_id}`, { replace: true });
      }

      // Replace temp msg + add AI response
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempUserMsg.id),
        user_message,
        assistant_message
      ]);

    } catch (err) {
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
      toast.error(err.response?.data?.error || 'Failed to get answer');
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    "What are the main topics covered in my documents?",
    "Can you summarize the key findings?",
    "What does the document say about...",
    "Explain the concept of..."
  ];

  return (
    <div className="layout">
      <Navbar />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-0)' }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-1)',
          display: 'flex', alignItems: 'center', gap: 12
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-0)', fontSize: 15 }}>
              {currentSession?.title || 'New Conversation'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-3)' }}>AI Knowledge Assistant</div>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {loadingSession ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <div className="spinner" style={{ width: 32, height: 32 }} />
            </div>
          ) : messages.length === 0 ? (
            <div style={{ textAlign: 'center', maxWidth: 500, margin: '60px auto 0' }}>
              <div style={{
                width: 64, height: 64, margin: '0 auto 20px',
                background: 'linear-gradient(135deg, rgba(108,99,255,0.2), rgba(167,139,250,0.1))',
                borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1px solid rgba(108,99,255,0.3)'
              }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-0)', marginBottom: 10 }}>
                Ask your documents anything
              </h2>
              <p style={{ color: 'var(--text-3)', fontSize: 14, lineHeight: 1.7 }}>
                Your AI assistant will search through your uploaded documents and provide accurate answers with source references.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 24 }}>
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(s)}
                    style={{
                      padding: '10px 16px', background: 'var(--bg-2)',
                      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-2)', cursor: 'pointer', fontSize: 13,
                      textAlign: 'left', transition: 'all 0.15s ease',
                      fontFamily: 'var(--font-display)'
                    }}
                    onMouseEnter={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.color = 'var(--text-0)'; }}
                    onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-2)'; }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <Message key={msg.id} msg={msg} />
              ))}
              {loading && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 20, animation: 'fadeIn 0.25s ease' }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%', flexShrink: 0, marginTop: 4,
                    background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                  </div>
                  <div style={{
                    padding: '14px 18px', background: 'var(--bg-2)',
                    borderRadius: '18px 18px 18px 4px', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', gap: 6
                  }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{
                        width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)',
                        animation: `pulse-glow 1.2s ease infinite`,
                        animationDelay: `${i * 0.2}s`,
                        opacity: 0.7
                      }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div style={{
          padding: '16px 24px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-1)'
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents... (Enter to send, Shift+Enter for newline)"
              rows={1}
              style={{
                flex: 1,
                background: 'var(--bg-2)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '12px 16px',
                color: 'var(--text-0)',
                fontFamily: 'var(--font-display)',
                fontSize: 14,
                resize: 'none',
                outline: 'none',
                transition: 'border-color 0.2s',
                maxHeight: 120,
                lineHeight: 1.5
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="btn btn-primary"
              style={{ height: 44, padding: '0 20px', flexShrink: 0 }}
            >
              {loading ? (
                <div className="spinner" style={{ width: 16, height: 16 }} />
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}