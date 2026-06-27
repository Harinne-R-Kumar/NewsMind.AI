/**
 * NewsMind AI - Profile Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, LogOut, Trash2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';


export default function Profile() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showConfirm, setShowConfirm] = useState(false);
  const [verified, setVerified] = useState(user?.is_verified);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  const handleDeleteAccount = async () => {
    const confirmDelete = window.confirm(
      "Are you sure?\n\nThis action cannot be undone."
    );
  
    if (!confirmDelete) return;
  
    try {
      await authAPI.deleteAccount();
  
      logout(); // clears auth context
  
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
  
      alert("Account deleted successfully.");
  
      navigate("/");
    } catch (err) {
      console.error(err);
      alert("Failed to delete account.");
    }
  };
  const handleResendVerification = async () => {
    try {
      await authAPI.resendVerification();
  
      alert(
        "Verification email sent.\nPlease check your inbox and spam folder."
      );
    } catch (err) {
      console.error(err);
      alert("Unable to send verification email.");
    }
  };
  useEffect(() => {
    const loadUser = async () => {
      try {
        const { data } = await authAPI.me();
        setVerified(data.is_verified);
      } catch (err) {
        console.error(err);
      }
    };
  
    loadUser();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-md mx-auto">
        <h1 className="text-2xl font-bold mb-6">Profile</h1>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-brand-500 to-indigo-500 flex items-center justify-center text-2xl font-bold">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div>
              <h2 className="text-xl font-semibold">{user?.name || 'User'}</h2>
              <p className="text-slate-400">{user?.email || ''}</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="p-3 bg-slate-800 rounded-xl">
              <div className="text-sm text-slate-400">User ID</div>
              <div className="font-mono">{user?.id || '-'}</div>
            </div>
            <div className="p-3 bg-slate-800 rounded-xl">
              <div className="text-sm text-slate-400">Email Verified</div>
                <div>

            {verified ? (

                <span className="text-green-500 font-semibold">

                    ✅ Verified

                </span>

            ) : (

                <div className="space-y-3">

                    <div className="text-red-500">

                        ❌ Not Verified

                    </div>

                    <button

                        onClick={handleResendVerification}

                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"

                    >

                        Resend Verification Email

                    </button>

                </div>

            )}

            </div>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>

          <button
            onClick={handleDeleteAccount}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
          >
            <Trash2 className="w-5 h-5" />
            Delete Account
          </button>
        </div>

        <div className="mt-8 p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <p className="text-slate-400 text-sm text-center">
            NewsMind AI - Your Personal Intelligence Agent
          </p>
          <p className="text-slate-500 text-xs text-center mt-2">
            Powered by LangGraph, MCP, and Ollama
          </p>
        </div>
      </div>
    </div>
  );
}
