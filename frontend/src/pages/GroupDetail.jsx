import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getGroupDetail, getBalances, getSettlements, uploadCSV, getImports, getImportReport } from '../api';
import toast from 'react-hot-toast';
import { HiOutlineArrowRight, HiOutlineCloudArrowUp, HiOutlineDocumentMagnifyingGlass, HiOutlineExclamationTriangle, HiOutlineCheckCircle, HiOutlineBanknotes, HiOutlineUserGroup, HiOutlineArrowsRightLeft } from 'react-icons/hi2';

export default function GroupDetail() {
  const { groupId } = useParams();
  const [group, setGroup] = useState(null);
  const [balances, setBalances] = useState(null);
  const [settlements, setSettlements] = useState([]);
  const [imports, setImports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [tab, setTab] = useState('balances');
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileRef = useRef();

  useEffect(() => { loadData(); }, [groupId]);

  const loadData = async () => {
    try {
      const [gRes, bRes, sRes, iRes] = await Promise.all([
        getGroupDetail(groupId),
        getBalances(groupId),
        getSettlements(groupId),
        getImports(groupId),
      ]);
      setGroup(gRes.data);
      setBalances(bRes.data);
      setSettlements(sRes.data);
      setImports(iRes.data);
    } catch (err) {
      toast.error('Failed to load group data');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    try {
      const res = await uploadCSV(groupId, selectedFile);
      toast.success(`Import complete! ${res.data.successful_rows} rows imported, ${res.data.failed_rows} issues found.`);
      setSelectedFile(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
    } finally {
      setUploading(false);
    }
  };

  const viewReport = async (sessionId) => {
    try {
      const res = await getImportReport(groupId, sessionId);
      setActiveReport(res.data);
    } catch (err) {
      toast.error('Failed to load report');
    }
  };

  if (!group) return <div className="loading-page"><div className="spinner"></div></div>;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h2>{group.name}</h2>
        <p>{group.memberships?.filter(m => !m.left_at).length || 0} active members</p>
      </div>

      <div className="tabs">
        {['balances', 'import', 'members'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'balances' ? '💰 Balances' : t === 'import' ? '📥 Import' : '👥 Members'}
          </div>
        ))}
      </div>

      {tab === 'balances' && balances && (
        <div className="slide-up">
          <div className="stats-grid">
            <div className="glass-card stat-card">
              <div className="stat-icon green"><HiOutlineBanknotes /></div>
              <div className="stat-value">{balances.balances?.length || 0}</div>
              <div className="stat-label">People Involved</div>
            </div>
            <div className="glass-card stat-card">
              <div className="stat-icon purple"><HiOutlineArrowsRightLeft /></div>
              <div className="stat-value">{balances.suggested_settlements?.length || 0}</div>
              <div className="stat-label">Settlements Needed</div>
            </div>
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Net Balances</h3>
          <div className="glass-card" style={{ padding: 0, marginBottom: 24, overflow: 'hidden' }}>
            <table className="data-table">
              <thead><tr><th>Person</th><th>Email</th><th style={{textAlign:'right'}}>Net Balance</th></tr></thead>
              <tbody>
                {balances.balances?.map(b => (
                  <tr key={b.user.id}>
                    <td style={{ fontWeight: 600 }}>{b.user.username}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{b.user.email}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700 }} className={b.net_balance >= 0 ? 'balance-positive' : 'balance-negative'}>
                      {b.net_balance >= 0 ? '+' : ''}₹{b.net_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Suggested Settlements</h3>
          {balances.suggested_settlements?.length === 0 ? (
            <div className="glass-card empty-state"><div className="empty-icon">✅</div><h3>All settled!</h3><p>No pending debts in this group.</p></div>
          ) : (
            balances.suggested_settlements?.map((s, i) => (
              <div key={i} className="glass-card settlement-card">
                <div className="settlement-arrow">
                  <span className="settlement-user">{s.from_user.username}</span>
                  <HiOutlineArrowRight style={{ color: 'var(--accent-purple)', fontSize: 20 }} />
                  <span className="settlement-user">{s.to_user.username}</span>
                </div>
                <div className="settlement-amount">₹{s.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'import' && (
        <div className="slide-up">
          <div className="glass-card" style={{ marginBottom: 24 }}>
            <div className="upload-zone" onClick={() => fileRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); setSelectedFile(e.dataTransfer.files[0]); }}>
              <input ref={fileRef} type="file" accept=".csv" hidden onChange={e => setSelectedFile(e.target.files[0])} />
              <div className="upload-icon"><HiOutlineCloudArrowUp /></div>
              <p>Drag & drop your CSV file here, or click to browse</p>
              {selectedFile && <div className="file-name">{selectedFile.name}</div>}
            </div>
            {selectedFile && (
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16 }}>
                <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
                  {uploading ? 'Importing...' : 'Import CSV'}
                </button>
              </div>
            )}
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Import History</h3>
          {imports.length === 0 ? (
            <div className="glass-card empty-state"><div className="empty-icon">📂</div><h3>No imports yet</h3><p>Upload a CSV file to get started.</p></div>
          ) : (
            imports.map(imp => (
              <div key={imp.id} className="glass-card" style={{ padding: 20, marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{imp.file_name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {new Date(imp.uploaded_at).toLocaleString()} · <span className="badge badge-green">{imp.successful_rows} imported</span> <span className="badge badge-red" style={{ marginLeft: 4 }}>{imp.failed_rows} issues</span>
                  </div>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => viewReport(imp.id)}><HiOutlineDocumentMagnifyingGlass /> View Report</button>
              </div>
            ))
          )}

          {activeReport && (
            <div className="modal-overlay" onClick={() => setActiveReport(null)}>
              <div className="glass-card modal-content" style={{ maxWidth: 700, maxHeight: '85vh' }} onClick={e => e.stopPropagation()}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><HiOutlineDocumentMagnifyingGlass /> Import Audit Report</h3>
                <div className="stats-grid" style={{ marginBottom: 20 }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 24, fontWeight: 800 }}>{activeReport.total_rows}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total Rows</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-green)' }}>{activeReport.successful_rows}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Imported</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-red)' }}>{activeReport.failed_rows}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Issues</div>
                  </div>
                </div>
                <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: 'var(--text-secondary)' }}>Detected Anomalies ({activeReport.issues?.length || 0})</h4>
                <div style={{ maxHeight: '50vh', overflowY: 'auto' }}>
                  {activeReport.issues?.map((iss, i) => (
                    <div key={i} className={`glass-card issue-card ${iss.issue_type}`}>
                      <div className="issue-row-num">Row {iss.row_number} · <span className="badge badge-orange" style={{ fontSize: 10 }}>{iss.issue_type.replace(/_/g, ' ').toUpperCase()}</span></div>
                      <div className="issue-desc">{iss.description}</div>
                      {iss.suggested_action && <div className="issue-action">💡 {iss.suggested_action}</div>}
                    </div>
                  ))}
                </div>
                <div className="modal-actions">
                  <button className="btn btn-secondary" onClick={() => setActiveReport(null)}>Close</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'members' && (
        <div className="slide-up">
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Group Members</h3>
          <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead><tr><th>Name</th><th>Email</th><th>Joined</th><th>Left</th><th>Status</th></tr></thead>
              <tbody>
                {group.memberships?.map(m => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>{m.user.username}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{m.user.email}</td>
                    <td>{new Date(m.joined_at).toLocaleDateString()}</td>
                    <td>{m.left_at ? new Date(m.left_at).toLocaleDateString() : '—'}</td>
                    <td>{m.left_at ? <span className="badge badge-red">Left</span> : <span className="badge badge-green">Active</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
