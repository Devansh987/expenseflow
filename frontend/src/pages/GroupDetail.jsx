import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getGroupDetail, getBalances, getSettlements, uploadCSV, getImports, getImportReport, getExpenses, createExpense, addMember, createSettlement } from '../api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { HiOutlineArrowRight, HiOutlineCloudArrowUp, HiOutlineDocumentMagnifyingGlass, HiOutlineBanknotes, HiOutlineUserGroup, HiOutlineArrowsRightLeft, HiOutlinePlusCircle, HiOutlineUserPlus, HiOutlineCheckCircle } from 'react-icons/hi2';

export default function GroupDetail() {
  const { groupId } = useParams();
  const { user } = useAuth();
  
  const [group, setGroup] = useState(null);
  const [balances, setBalances] = useState(null);
  const [settlements, setSettlements] = useState([]);
  const [imports, setImports] = useState([]);
  const [expenses, setExpenses] = useState([]);
  
  const [activeReport, setActiveReport] = useState(null);
  const [tab, setTab] = useState('expenses');
  
  // Modals
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);
  
  // Forms
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [expenseForm, setExpenseForm] = useState({
    description: '',
    amount: '',
    currency: 'INR',
    expense_date: new Date().toISOString().split('T')[0],
    payer_id: user?.id || '',
    split_type: 'EQUAL'
  });
  const [splitDetails, setSplitDetails] = useState({}); // { user_id: value }
  
  // CSV Upload
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileRef = useRef();

  useEffect(() => { loadData(); }, [groupId]);

  const loadData = async () => {
    try {
      const [gRes, bRes, sRes, iRes, eRes] = await Promise.all([
        getGroupDetail(groupId),
        getBalances(groupId),
        getSettlements(groupId),
        getImports(groupId),
        getExpenses(groupId)
      ]);
      setGroup(gRes.data);
      setBalances(bRes.data);
      setSettlements(sRes.data);
      setImports(iRes.data);
      setExpenses(eRes.data);
      
      // Initialize default payer if not set
      if (!expenseForm.payer_id && user) {
        setExpenseForm(prev => ({ ...prev, payer_id: user.id }));
      }
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

  const handleAddMember = async (e) => {
    e.preventDefault();
    try {
      await addMember(groupId, newMemberEmail);
      toast.success('Member added successfully');
      setNewMemberEmail('');
      setShowMemberModal(false);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add member');
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    
    // Prepare split details if not EQUAL
    const splits = [];
    if (expenseForm.split_type !== 'EQUAL') {
      for (const [userId, val] of Object.entries(splitDetails)) {
        if (val) {
          splits.push({
            user_id: userId,
            share_percentage: expenseForm.split_type === 'PERCENTAGE' ? parseFloat(val) : null,
            share_ratio: expenseForm.split_type === 'SHARES' ? parseFloat(val) : null
          });
        }
      }
      
      // Basic validation
      if (expenseForm.split_type === 'PERCENTAGE') {
        const sum = splits.reduce((acc, s) => acc + (s.share_percentage || 0), 0);
        if (Math.abs(sum - 100) > 0.01) {
          toast.error(`Percentages must add up to 100. Current sum: ${sum}`);
          return;
        }
      }
    }

    try {
      await createExpense(groupId, {
        ...expenseForm,
        amount: parseFloat(expenseForm.amount),
        splits: splits.length > 0 ? splits : null
      });
      toast.success('Expense added!');
      setShowExpenseModal(false);
      setExpenseForm({ ...expenseForm, description: '', amount: '' });
      setSplitDetails({});
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add expense');
    }
  };

  const handleSettleUp = async (settlement) => {
    try {
      await createSettlement(groupId, {
        to_user_id: settlement.to_user.id,
        amount: settlement.amount,
        currency: 'INR'
      });
      toast.success(`Settled ₹${settlement.amount} with ${settlement.to_user.username}`);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to settle up');
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
        {['expenses', 'balances', 'import', 'members'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'expenses' ? '📄 Expenses' : t === 'balances' ? '💰 Balances' : t === 'import' ? '📥 Import' : '👥 Members'}
          </div>
        ))}
      </div>

      {tab === 'expenses' && (
        <div className="slide-up">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Group Expenses</h3>
            <button className="btn btn-primary" onClick={() => setShowExpenseModal(true)}><HiOutlinePlusCircle /> Add Expense</button>
          </div>
          
          {expenses.length === 0 ? (
            <div className="glass-card empty-state">
              <div className="empty-icon">💸</div>
              <h3>No expenses yet</h3>
              <p>Add an expense manually or import a CSV</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {expenses.map(exp => (
                <div key={exp.id} className="glass-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{exp.description}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      {new Date(exp.expense_date).toLocaleDateString()} · Paid by {exp.payer?.username}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 800, fontSize: 18, color: exp.payer_id === user?.id ? 'var(--accent-green)' : 'var(--text-primary)' }}>
                      ₹{exp.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="badge badge-orange" style={{ marginTop: 4, display: 'inline-block', fontSize: 10 }}>{exp.split_type}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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
              <thead><tr><th>Person</th><th style={{textAlign:'right'}}>Net Balance</th></tr></thead>
              <tbody>
                {balances.balances?.map(b => (
                  <tr key={b.user.id}>
                    <td style={{ fontWeight: 600 }}>{b.user.username} {b.user.id === user?.id ? '(You)' : ''}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700 }} className={b.net_balance > 0 ? 'balance-positive' : b.net_balance < 0 ? 'balance-negative' : ''}>
                      {b.net_balance > 0 ? '+' : ''}₹{b.net_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
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
              <div key={i} className="glass-card settlement-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div className="settlement-arrow">
                    <span className="settlement-user">{s.from_user.username} {s.from_user.id === user?.id ? '(You)' : ''}</span>
                    <HiOutlineArrowRight style={{ color: 'var(--accent-purple)', fontSize: 20 }} />
                    <span className="settlement-user">{s.to_user.username} {s.to_user.id === user?.id ? '(You)' : ''}</span>
                  </div>
                  <div className="settlement-amount" style={{ marginLeft: 16 }}>₹{s.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
                </div>
                {s.from_user.id === user?.id && (
                  <button className="btn btn-primary btn-sm" onClick={() => handleSettleUp(s)}>
                    <HiOutlineCheckCircle /> Settle Up
                  </button>
                )}
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
        </div>
      )}

      {tab === 'members' && (
        <div className="slide-up">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Group Members</h3>
            <button className="btn btn-primary" onClick={() => setShowMemberModal(true)}><HiOutlineUserPlus /> Add Member</button>
          </div>
          <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead><tr><th>Name</th><th>Email</th><th>Joined</th><th>Status</th></tr></thead>
              <tbody>
                {group.memberships?.map(m => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>{m.user.username} {m.user.id === user?.id ? '(You)' : ''}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{m.user.email}</td>
                    <td>{new Date(m.joined_at).toLocaleDateString()}</td>
                    <td>{m.left_at ? <span className="badge badge-red">Left</span> : <span className="badge badge-green">Active</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Modals Below */}

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
            <div style={{ maxHeight: '40vh', overflowY: 'auto' }}>
              {activeReport.issues?.length === 0 ? (
                <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>No issues found! All rows imported successfully.</div>
              ) : (
                activeReport.issues?.map((iss, i) => (
                  <div key={i} className={`glass-card issue-card ${iss.issue_type}`}>
                    <div className="issue-row-num">Row {iss.row_number} · <span className="badge badge-orange" style={{ fontSize: 10 }}>{iss.issue_type.replace(/_/g, ' ').toUpperCase()}</span></div>
                    <div className="issue-desc">{iss.description}</div>
                    {iss.suggested_action && <div className="issue-action">💡 {iss.suggested_action}</div>}
                  </div>
                ))
              )}
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setActiveReport(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {showMemberModal && (
        <div className="modal-overlay" onClick={() => setShowMemberModal(false)}>
          <div className="glass-card modal-content" onClick={e => e.stopPropagation()}>
            <h3>Add Member to Group</h3>
            <form onSubmit={handleAddMember}>
              <div className="input-group">
                <label>User Email Address</label>
                <input className="input-field" type="email" placeholder="friend@example.com" value={newMemberEmail} onChange={e => setNewMemberEmail(e.target.value)} required autoFocus />
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>The user must already have an account on ExpenseFlow.</p>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowMemberModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Member</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showExpenseModal && (
        <div className="modal-overlay" onClick={() => setShowExpenseModal(false)}>
          <div className="glass-card modal-content" style={{ maxWidth: 500, maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <h3>Add New Expense</h3>
            <form onSubmit={handleAddExpense}>
              <div className="input-group">
                <label>Description</label>
                <input className="input-field" placeholder="e.g. Groceries" value={expenseForm.description} onChange={e => setExpenseForm({...expenseForm, description: e.target.value})} required autoFocus />
              </div>
              
              <div style={{ display: 'flex', gap: 16 }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Amount</label>
                  <input className="input-field" type="number" step="0.01" min="0" placeholder="0.00" value={expenseForm.amount} onChange={e => setExpenseForm({...expenseForm, amount: e.target.value})} required />
                </div>
                <div className="input-group" style={{ width: 100 }}>
                  <label>Currency</label>
                  <select className="input-field" value={expenseForm.currency} onChange={e => setExpenseForm({...expenseForm, currency: e.target.value})}>
                    <option value="INR">INR</option>
                    <option value="USD">USD</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 16 }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Date</label>
                  <input className="input-field" type="date" value={expenseForm.expense_date} onChange={e => setExpenseForm({...expenseForm, expense_date: e.target.value})} required />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Paid By</label>
                  <select className="input-field" value={expenseForm.payer_id} onChange={e => setExpenseForm({...expenseForm, payer_id: e.target.value})} required>
                    {group.memberships?.filter(m => !m.left_at).map(m => (
                      <option key={m.user.id} value={m.user.id}>{m.user.username} {m.user.id === user?.id ? '(You)' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label>Split Type</label>
                <select className="input-field" value={expenseForm.split_type} onChange={e => setExpenseForm({...expenseForm, split_type: e.target.value})}>
                  <option value="EQUAL">Split Equally</option>
                  <option value="PERCENTAGE">Split by Percentage</option>
                  <option value="SHARES">Split by Exact Shares</option>
                </select>
              </div>

              {expenseForm.split_type !== 'EQUAL' && (
                <div className="split-details-container glass-card" style={{ padding: 16, marginBottom: 20, background: 'rgba(255,255,255,0.02)' }}>
                  <h4 style={{ fontSize: 13, marginBottom: 12 }}>Enter {expenseForm.split_type === 'PERCENTAGE' ? 'Percentages (must equal 100%)' : 'Shares (e.g. 1, 2, 0.5)'}</h4>
                  {group.memberships?.filter(m => !m.left_at).map(m => (
                    <div key={m.user.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontSize: 14 }}>{m.user.username}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <input 
                          type="number" 
                          step="0.01" 
                          min="0"
                          className="input-field" 
                          style={{ width: 100, padding: '6px 12px' }} 
                          placeholder="0"
                          value={splitDetails[m.user.id] || ''}
                          onChange={e => setSplitDetails({...splitDetails, [m.user.id]: e.target.value})}
                        />
                        <span style={{ color: 'var(--text-muted)' }}>{expenseForm.split_type === 'PERCENTAGE' ? '%' : 'shares'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowExpenseModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Expense</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
