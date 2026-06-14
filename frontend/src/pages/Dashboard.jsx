import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGroups, createGroup } from '../api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { HiOutlineUserGroup, HiOutlinePlusCircle, HiOutlineBanknotes, HiOutlineArrowTrendingUp } from 'react-icons/hi2';

export default function Dashboard() {
  const [groups, setGroups] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [groupName, setGroupName] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { loadGroups(); }, []);

  const loadGroups = async () => {
    try {
      const res = await getGroups();
      setGroups(res.data);
    } catch (err) {
      toast.error('Failed to load groups');
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createGroup(groupName);
      toast.success('Group created!');
      setShowModal(false);
      setGroupName('');
      loadGroups();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create group');
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Welcome back, {user?.username}! Manage your shared expenses.</p>
      </div>
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon purple"><HiOutlineUserGroup /></div>
          <div className="stat-value">{groups.length}</div>
          <div className="stat-label">Active Groups</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon cyan"><HiOutlineBanknotes /></div>
          <div className="stat-value">₹0</div>
          <div className="stat-label">Total Expenses</div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon green"><HiOutlineArrowTrendingUp /></div>
          <div className="stat-value">0</div>
          <div className="stat-label">Settlements</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700 }}>Your Groups</h3>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><HiOutlinePlusCircle /> New Group</button>
      </div>

      {groups.length === 0 ? (
        <div className="glass-card empty-state">
          <div className="empty-icon">👥</div>
          <h3>No groups yet</h3>
          <p>Create your first group to start tracking expenses</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {groups.map(g => (
            <div key={g.id} className="glass-card" style={{ padding: 24, cursor: 'pointer' }} onClick={() => navigate(`/groups/${g.id}`)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>👥</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{g.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Created {new Date(g.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="glass-card modal-content" onClick={e => e.stopPropagation()}>
            <h3>Create New Group</h3>
            <form onSubmit={handleCreate}>
              <div className="input-group">
                <label>Group Name</label>
                <input className="input-field" placeholder="e.g. Flatmates" value={groupName} onChange={e => setGroupName(e.target.value)} required autoFocus />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Group</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
