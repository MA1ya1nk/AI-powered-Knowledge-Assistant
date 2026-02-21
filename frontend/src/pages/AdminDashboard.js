// pages/AdminDashboard.js
import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { adminAPI } from '../services/api';
import toast from 'react-hot-toast';

function Tab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
        fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600,
        color: active ? 'var(--accent-2)' : 'var(--text-3)',
        borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
        transition: 'all 0.15s ease'
      }}
    >
      {label}
    </button>
  );
}

function StatCard({ label, value, sub, color = 'var(--accent)' }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--text-0)', fontFamily: 'var(--font-mono)' }}>{value}</div>
      <div style={{ fontSize: 13, color: 'var(--text-2)', marginTop: 6 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color, marginTop: 4, fontWeight: 600 }}>{sub}</div>}
    </div>
  );
}

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.stats()
      .then(res => setStats(res.data))
      .catch(() => toast.error('Failed to load stats'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (activeTab === 'users' && users.length === 0) {
      adminAPI.listUsers().then(res => setUsers(res.data.users)).catch(() => toast.error('Failed to load users'));
    }
    if (activeTab === 'documents' && documents.length === 0) {
      adminAPI.listDocuments().then(res => setDocuments(res.data.documents)).catch(() => toast.error('Failed to load documents'));
    }
    if (activeTab === 'queries' && queries.length === 0) {
      adminAPI.listQueries().then(res => setQueries(res.data.messages)).catch(() => toast.error('Failed to load queries'));
    }
  }, [activeTab]);

  const toggleUser = async (user) => {
    try {
      await adminAPI.toggleUser(user.id);
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, is_active: !u.is_active } : u));
      toast.success(`User ${user.is_active ? 'disabled' : 'enabled'}`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to toggle user');
    }
  };

  const toggleDocument = async (doc) => {
    try {
      await adminAPI.toggleDocument(doc.id);
      setDocuments(prev => prev.map(d => d.id === doc.id
        ? { ...d, is_active: !d.is_active, status: d.is_active ? 'disabled' : 'ready' }
        : d));
      toast.success(`Document ${doc.is_active ? 'disabled' : 'enabled'}`);
    } catch {
      toast.error('Failed to toggle document');
    }
  };

  return (
    <div className="layout">
      <Navbar />
      <main className="main-content" style={{ padding: 32 }}>
        <div style={{ marginBottom: 28, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            padding: '4px 10px', borderRadius: 6,
            background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)',
            color: '#f59e0b', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em'
          }}>ADMIN</div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-0)' }}>
            Control Panel
          </h1>
        </div>

        {/* Tabs */}
        <div style={{ borderBottom: '1px solid var(--border)', marginBottom: 28, display: 'flex' }}>
          {['overview', 'users', 'documents', 'queries'].map(tab => (
            <Tab key={tab} label={tab.charAt(0).toUpperCase() + tab.slice(1)} active={activeTab === tab} onClick={() => setActiveTab(tab)} />
          ))}
        </div>

        {/* Overview */}
        {activeTab === 'overview' && (
          loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
              {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: 100, borderRadius: 'var(--radius)' }} />)}
            </div>
          ) : stats && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
                <StatCard label="Total Users" value={stats.users.total} sub={`${stats.users.active} active`} color="var(--green)" />
                <StatCard label="Documents" value={stats.documents.total} sub={`${stats.documents.by_status.ready || 0} ready`} color="var(--accent)" />
                <StatCard label="Total Chunks" value={stats.documents.total_chunks} />
                <StatCard label="Conversations" value={stats.conversations.total_sessions} sub={`${stats.conversations.total_messages} messages`} color="#a78bfa" />
                <StatCard label="Total Queries" value={stats.usage.total_queries} />
                <StatCard label="Est. Cost (USD)" value={`$${stats.usage.estimated_cost_usd}`} sub={`${stats.usage.total_tokens.toLocaleString()} tokens`} color="var(--yellow)" />
              </div>

              {stats.recent_queries?.length > 0 && (
                <>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-0)', marginBottom: 14 }}>Recent Queries</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {stats.recent_queries.map((q, i) => (
                      <div key={i} style={{
                        padding: '12px 16px', background: 'var(--bg-2)',
                        border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                        display: 'flex', gap: 12, alignItems: 'center'
                      }}>
                        <span style={{ color: 'var(--text-3)', fontSize: 12, fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                          {new Date(q.created_at).toLocaleTimeString()}
                        </span>
                        <span style={{ color: 'var(--text-1)', fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {q.content}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )
        )}

        {/* Users */}
        {activeTab === 'users' && (
          <div>
            <div style={{ marginBottom: 16, color: 'var(--text-3)', fontSize: 13 }}>{users.length} users</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {users.map(user => (
                <div key={user.id} className="card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: '50%', flexShrink: 0,
                    background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontWeight: 700, fontSize: 15
                  }}>
                    {user.username[0].toUpperCase()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-0)', fontSize: 14 }}>{user.username}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>{user.email}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span className={`badge ${user.role === 'admin' ? 'badge-yellow' : 'badge-blue'}`}>{user.role}</span>
                    <span className={`badge ${user.is_active ? 'badge-green' : 'badge-red'}`}>
                      {user.is_active ? 'Active' : 'Disabled'}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{user.total_queries} queries</span>
                    {user.role !== 'admin' && (
                      <button
                        onClick={() => toggleUser(user)}
                        className={`btn btn-sm ${user.is_active ? 'btn-danger' : 'btn-ghost'}`}
                      >
                        {user.is_active ? 'Disable' : 'Enable'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Documents */}
        {activeTab === 'documents' && (
          <div>
            <div style={{ marginBottom: 16, color: 'var(--text-3)', fontSize: 13 }}>{documents.length} documents</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {documents.map(doc => (
                <div key={doc.id} className="card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{
                    padding: '4px 8px', background: 'var(--bg-3)',
                    borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
                    color: doc.file_type === 'pdf' ? 'var(--red)' : 'var(--accent)', flexShrink: 0
                  }}>
                    {doc.file_type?.toUpperCase()}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-0)', fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.original_name}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>
                      by {doc.uploaded_by} · {doc.chunk_count} chunks
                    </div>
                  </div>
                  <span className={`badge ${doc.status === 'ready' ? 'badge-green' : doc.status === 'error' ? 'badge-red' : doc.status === 'disabled' ? 'badge-gray' : 'badge-yellow'}`}>
                    {doc.status}
                  </span>
                  {['ready', 'disabled'].includes(doc.status) && (
                    <button
                      onClick={() => toggleDocument(doc)}
                      className={`btn btn-sm ${doc.is_active ? 'btn-danger' : 'btn-ghost'}`}
                    >
                      {doc.is_active ? 'Disable' : 'Enable'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Queries */}
        {activeTab === 'queries' && (
          <div>
            <div style={{ marginBottom: 16, color: 'var(--text-3)', fontSize: 13 }}>{queries.length} messages</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {queries.map(msg => (
                <div key={msg.id} style={{
                  padding: '12px 16px', background: 'var(--bg-2)',
                  border: `1px solid ${msg.role === 'user' ? 'var(--border)' : 'rgba(108,99,255,0.2)'}`,
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: `3px solid ${msg.role === 'user' ? 'var(--border-bright)' : 'var(--accent)'}`
                }}>
                  <div style={{ display: 'flex', gap: 12, marginBottom: 6, alignItems: 'center' }}>
                    <span className={`badge ${msg.role === 'user' ? 'badge-blue' : 'badge-green'}`}>{msg.role}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{msg.username}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-3)', marginLeft: 'auto' }}>
                      {msg.tokens_used > 0 && `${msg.tokens_used} tokens · `}
                      {new Date(msg.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ fontSize: 14, color: 'var(--text-1)', lineHeight: 1.5 }}>
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}