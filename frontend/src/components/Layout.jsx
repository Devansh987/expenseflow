import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HiOutlineSparkles, HiOutlineSquares2X2, HiOutlineUserGroup, HiOutlineArrowRightOnRectangle } from 'react-icons/hi2';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon"><HiOutlineSparkles /></div>
          <h1>ExpenseFlow</h1>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <HiOutlineSquares2X2 className="nav-icon" />
            Dashboard
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div className="user-details">
              <div className="name">{user?.username}</div>
              <div className="email">{user?.email}</div>
            </div>
          </div>
          <button className="btn btn-secondary" style={{ width: '100%', marginTop: 12 }} onClick={handleLogout}>
            <HiOutlineArrowRightOnRectangle /> Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
