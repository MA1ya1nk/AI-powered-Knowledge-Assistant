// pages/Documents.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Navbar from '../components/Navbar';
import { documentsAPI } from '../services/api';
import toast from 'react-hot-toast';

function StatusBadge({ status }) {
  const map = {
    ready: ['badge-green', '✓ Ready'],
    processing: ['badge-yellow', '⟳ Processing'],
    error: ['badge-red', '✗ Error'],
    disabled: ['badge-gray', '⊘ Disabled'],
  };
  const [cls, label] = map[status] || ['badge-gray', status];
  return <span className={`badge ${cls}`}>{label}</span>;
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [pollingIds, setPollingIds] = useState(new Set());
  const fileInputRef = useRef();

  const fetchDocs = useCallback(async () => {
    try {
      const res = await documentsAPI.list();
      setDocuments(res.data.documents);
    } catch (err) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  // Poll processing documents
  useEffect(() => {
    const processingDocs = documents.filter(d => d.status === 'processing');
    if (processingDocs.length === 0) return;

    let attempts = {};

    const interval = setInterval(async () => {
      for (const doc of processingDocs) {
        attempts[doc.id] = (attempts[doc.id] || 0) + 1;

        // Stop polling after 20 attempts (1 minute)
        if (attempts[doc.id] > 20) {
          setDocuments(prev => prev.map(d =>
            d.id === doc.id && d.status === 'processing'
              ? { ...d, status: 'error', error_message: 'Processing timeout' }
              : d
          ));
          continue;
        }

        try {
          const res = await documentsAPI.checkStatus(doc.id);
          if (res.data.status !== 'processing') {
            setDocuments(prev => prev.map(d =>
              d.id === doc.id
                ? { ...d, status: res.data.status, chunk_count: res.data.chunk_count, error_message: res.data.error_message }
                : d
            ));
            if (res.data.status === 'ready') {
              toast.success(`"${doc.original_name}" is ready!`);
            } else if (res.data.status === 'error') {
              toast.error(`"${doc.original_name}" processing failed`);
            }
          }
        } catch {}
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleUpload = async (file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'txt'].includes(ext)) {
      toast.error('Only PDF and TXT files are allowed');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      toast.error('File too large (max 16MB)');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setUploadProgress(0);

    try {
      const res = await documentsAPI.upload(formData, setUploadProgress);
      setDocuments(prev => [res.data.document, ...prev]);
      toast.success('Document uploaded! Processing...');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.original_name}"?`)) return;
    try {
      await documentsAPI.delete(doc.id);
      setDocuments(prev => prev.filter(d => d.id !== doc.id));
      toast.success('Document deleted');
    } catch {
      toast.error('Delete failed');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  return (
    <div className="layout">
      <Navbar />
      <main className="main-content" style={{ padding: 32 }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-0)' }}>
            Documents
          </h1>
          <p style={{ color: 'var(--text-2)', marginTop: 6, fontSize: 14 }}>
            Upload files to build your knowledge base
          </p>
        </div>

        {/* Upload Zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)',
            padding: '40px 32px',
            textAlign: 'center',
            cursor: uploading ? 'default' : 'pointer',
            background: dragging ? 'rgba(108,99,255,0.06)' : 'var(--bg-1)',
            transition: 'all 0.2s ease',
            marginBottom: 28
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt"
            style={{ display: 'none' }}
            onChange={e => handleUpload(e.target.files[0])}
          />
          
          {uploading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
              <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
              <div style={{ color: 'var(--text-1)', fontWeight: 600 }}>Uploading... {uploadProgress}%</div>
              <div style={{
                width: '200px', height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%', background: 'var(--accent)',
                  width: `${uploadProgress}%`, transition: 'width 0.3s ease', borderRadius: 2
                }} />
              </div>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 12, color: dragging ? 'var(--accent)' : 'var(--text-3)' }}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <div style={{ fontWeight: 700, color: 'var(--text-0)', marginBottom: 6 }}>
                {dragging ? 'Drop it here!' : 'Drop file or click to upload'}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-3)' }}>
                PDF and TXT files — max 16MB
              </div>
            </>
          )}
        </div>

        {/* Documents List */}
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[...Array(3)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 76, borderRadius: 'var(--radius)' }} />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{ color: 'var(--text-3)', fontSize: 48, marginBottom: 16 }}>📄</div>
            <div style={{ fontWeight: 600, color: 'var(--text-1)', marginBottom: 8 }}>No documents yet</div>
            <div style={{ fontSize: 14, color: 'var(--text-3)' }}>Upload your first document to get started</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 4 }}>
              {documents.length} document{documents.length !== 1 ? 's' : ''}
            </div>
            {documents.map(doc => (
              <div key={doc.id} className="card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16 }}>
                {/* Icon */}
                <div style={{
                  width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                  background: doc.file_type === 'pdf' ? 'rgba(239,68,68,0.15)' : 'rgba(108,99,255,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: doc.file_type === 'pdf' ? 'var(--red)' : 'var(--accent)',
                  fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700
                }}>
                  {doc.file_type.toUpperCase()}
                </div>
                
                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 600, color: 'var(--text-0)', fontSize: 14,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                  }}>
                    {doc.original_name}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 3, display: 'flex', gap: 16 }}>
                    <span>{formatSize(doc.file_size)}</span>
                    {doc.chunk_count > 0 && <span>{doc.chunk_count} chunks</span>}
                    <span>{formatDate(doc.created_at)}</span>
                  </div>
                  {doc.error_message && (
                    <div style={{ fontSize: 12, color: 'var(--red)', marginTop: 4 }}>{doc.error_message}</div>
                  )}
                </div>
                
                <StatusBadge status={doc.status} />
                
                <button
                  onClick={() => handleDelete(doc)}
                  className="btn btn-ghost btn-sm"
                  style={{ color: 'var(--text-3)', border: 'none', padding: '6px 8px' }}
                  title="Delete"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
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