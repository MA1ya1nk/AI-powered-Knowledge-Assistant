// pages/Dashboard.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { documentsAPI, chatAPI } from '../services/api';

function StatCard({ label, value, icon, color = 'var(--accent)' }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <div style={{
        width: 48, height: 48, borderRadius: 14, flexShrink: 0,
        background: `${color}22`,
        border: `1px solid ${color}44`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: color
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-0)' }}>{value}</div>
        <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 2 }}>{label}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    Promise.all([documentsAPI.list(1, 100), chatAPI.listSessions(1)])
      .then(([docsRes, sessRes]) => {
        setStats({
          docs: docsRes.data.total,
          readyDocs: docsRes.data.documents.filter(d => d.status === 'ready').length,
          sessions: sessRes.data.total,
          queries: user.total_queries || 0,
          tokens: user.total_tokens_used || 0
        });
      })
      .catch(() => setStats({ docs: 0, readyDocs: 0, sessions: 0, queries: 0, tokens: 0 }));
  }, [user]);

  return (
    <div className="layout">
      <Navbar />
      <main className="main-content" style={{ padding: 32 }}>
        {/* Header */}
        <div style={{ marginBottom: 36 }}>
          <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 6, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Welcome back
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-0)' }}>
            {user?.username} 👋
          </h1>
          <p style={{ color: 'var(--text-2)', marginTop: 8, fontSize: 15 }}>
            Your AI-powered knowledge workspace is ready.
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 36 }}>
            <StatCard
              label="Documents Uploaded"
              value={stats.docs}
              color="var(--accent)"
              icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>}
            />
            <StatCard
              label="Ready to Query"
              value={stats.readyDocs}
              color="var(--green)"
              icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>}
            />
            <StatCard
              label="Conversations"
              value={stats.sessions}
              color="#a78bfa"
              icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>}
            />
            <StatCard
              label="Total Queries"
              value={stats.queries}
              color="var(--yellow)"
              icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>}
            />
          </div>
        )}

        {/* Quick Actions */}
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-0)', marginBottom: 16, letterSpacing: '-0.02em' }}>
          Quick Actions
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
          <QuickAction
            title="Upload Document"
            desc="Add PDF or TXT files to your knowledge base"
            color="var(--accent)"
            onClick={() => navigate('/documents')}
            icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>}
          />
          <QuickAction
            title="Ask a Question"
            desc="Start a new AI conversation about your documents"
            color="#a78bfa"
            onClick={() => navigate('/chat')}
            icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>}
          />
          <QuickAction
            title="View History"
            desc="Browse your previous conversations and answers"
            color="var(--green)"
            onClick={() => navigate('/history')}
            icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 0 .5-4.5"/><polyline points="3 3 3 7 7 7"/></svg>}
          />
        </div>

        {/* How it works */}
        <div className="card" style={{ marginTop: 32, background: 'linear-gradient(135deg, rgba(108,99,255,0.08), rgba(167,139,250,0.05))' }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-0)', marginBottom: 16 }}>
            How it works
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 20 }}>
            {[
              { step: '01', title: 'Upload Documents', desc: 'Add your PDFs or text files' },
              { step: '02', title: 'AI Processes', desc: 'Documents are chunked & embedded' },
              { step: '03', title: 'Ask Questions', desc: 'Query your knowledge base naturally' },
              { step: '04', title: 'Get Answers', desc: 'AI answers with cited sources' },
            ].map(({ step, title, desc }) => (
              <div key={step} style={{ display: 'flex', gap: 12 }}>
                <div style={{
                  fontSize: 11, fontWeight: 800, color: 'var(--accent)',
                  fontFamily: 'var(--font-mono)', opacity: 0.7, paddingTop: 2
                }}>{step}</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-0)', marginBottom: 4 }}>{title}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-3)' }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function QuickAction({ title, desc, color, onClick, icon }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'var(--bg-2)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: 24, textAlign: 'left',
        cursor: 'pointer', transition: 'all 0.2s ease', display: 'block', width: '100%'
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = color;
        e.currentTarget.style.background = `${color}0a`;
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.background = 'var(--bg-2)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ color, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-0)', marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 13, color: 'var(--text-3)' }}>{desc}</div>
    </button>
  );
}