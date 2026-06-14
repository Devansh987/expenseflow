import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register, login, getMe } from '../api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { HiOutlineSparkles } from 'react-icons/hi2';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (!isLogin) {
        await register(form);
        toast.success('Account created! Logging in...');
      }
      const res = await login(form.email, form.password);
      const token = res.data.access_token;
      
      // Set token first for getMe to work correctly with Axios interceptors
      localStorage.setItem('token', token);
      const meRes = await getMe();
      loginUser(token, meRes.data);
      toast.success('Welcome to ExpenseFlow!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container fade-in">
        <div className="auth-header">
          <div className="logo-big"><HiOutlineSparkles /></div>
          <h1>ExpenseFlow</h1>
          <p>Shared expenses, simplified.</p>
        </div>
        <div className="glass-card auth-form">
          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="input-group">
                <label>Username</label>
                <input className="input-field" placeholder="Enter username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required />
              </div>
            )}
            <div className="input-group">
              <label>Email</label>
              <input className="input-field" type="email" placeholder="you@email.com" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input className="input-field" type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required />
            </div>
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>
          <div className="auth-switch">
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <span onClick={() => setIsLogin(!isLogin)}>{isLogin ? 'Sign up' : 'Sign in'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
