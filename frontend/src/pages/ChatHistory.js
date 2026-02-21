// pages/ChatHistory.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { chatAPI } from '../services/api';
import { useChat } from '../context/ChatContext';
import toast from 'react-hot-toast';

function formatDate(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function ChatHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { setCurrentSession, setMessages } = useChat();

  useEffect(() => {
    chatAPI.listSessions()
      .then(res => setSessions(res.data.sessions))
      .catch(() => toast.error('Failed to load history'))
      .finally(() => setLoading(false));
  }, []);

  const handleOpen = async (session) => {
    try {
      const res = await chatAPI.getSession(session.id);
      setCurrentSession(res.data.session);
      setMessages(res.data.messages);
      navigate(`/chat/${session.id}`);
    } catch {
      toast.error('Failed to load session');
    }
  };

  const handleDelete = async (e, session) => {
    e.stopPropagation();
    if (!window.confirm(`Delete "${session.title}"?`)) return;
    try {
      await chatAPI.deleteSession(session.id);
      setSessions(prev => prev.filter(s => s.id !== session.id));
      toast.success('Conversation deleted');
    } catch {
      toast.error('Delete failed');
    }
  };

  return (
    <div className="layout">
      <Navbar />
      <main className="main-content" style={{ padding: 32 }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-0)' }}>
            Chat History
          </h1>
          <p style={{ color: 'var(--text-2)', marginTop: 6, fontSize: 14 }}>
            {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
          </p>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 'var(--radius)' }} />)}
          </div>
        ) : sessions.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
            <div style={{ fontWeight: 600, color: 'var(--text-1)', marginBottom: 8 }}>No conversations yet</div>
            <div style={{ fontSize: 14, color: 'var(--text-3)', marginBottom: 20 }}>Start chatting with your AI assistant</div>
            <button className="btn btn-primary" onClick={() => navigate('/chat')}>Start Conversation</button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {sessions.map(session => (
              <div
                key={session.id}
                onClick={() => handleOpen(session)}
                style={{
                  background: 'var(--bg-2)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)', padding: '16px 20px',
                  cursor: 'pointer', transition: 'all 0.15s ease',
                  display: 'flex', alignItems: 'center', gap: 16
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'rgba(108,99,255,0.05)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--bg-2)'; }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 12, flexShrink: 0,
                  background: 'rgba(108,99,255,0.15)', border: '1px solid rgba(108,99,255,0.3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)'
                }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 600, color: 'var(--text-0)', fontSize: 14, marginBottom: 4,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                  }}>
                    {session.title}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 16 }}>
                    <span>{session.message_count} messages</span>
                    <span>Updated {formatDate(session.updated_at)}</span>
                  </div>
                </div>
                
                <button
                  onClick={(e) => handleDelete(e, session)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-3)', padding: 6, borderRadius: 6,
                    transition: 'color 0.15s', flexShrink: 0
                  }}
                  onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
                  title="Delete"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}