/**
 * NewsMind AI - Dashboard Page
 * Main dashboard showing recent reports and quick actions.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Newspaper, RefreshCw, Download, Clock, Settings, Loader, AlertCircle } from 'lucide-react';
import { reportsAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const { data } = await reportsAPI.list();
      setReports(data);
    } catch (err) {
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await reportsAPI.generate();
      await loadReports();
    } catch (err) {
      setError('Failed to generate newspaper');
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold">Welcome back, {user?.name || 'User'}!</h1>
            <p className="text-slate-400">Here's your personalized intelligence dashboard.</p>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-brand-500 to-indigo-500 text-white rounded-xl hover:from-brand-600 hover:to-indigo-600 transition-all disabled:opacity-50"
          >
            {generating ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                Generate Today's Brief
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Link
            to="/preferences"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-brand-500/50 transition-colors flex items-center gap-4"
          >
            <div className="w-12 h-12 rounded-xl bg-brand-500/20 flex items-center justify-center">
              <Settings className="w-6 h-6 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold">Preferences</div>
              <div className="text-sm text-slate-400">Manage interests</div>
            </div>
          </Link>

          <Link
            to="/schedule"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-brand-500/50 transition-colors flex items-center gap-4"
          >
            <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
              <Clock className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="font-semibold">Schedule</div>
              <div className="text-sm text-slate-400">Delivery times</div>
            </div>
          </Link>

          <Link
            to="/reports"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-brand-500/50 transition-colors flex items-center gap-4"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <Newspaper className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="font-semibold">Reports</div>
              <div className="text-sm text-slate-400">View history</div>
            </div>
          </Link>
        </div>

        {/* Recent Reports */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Reports</h2>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="w-8 h-8 animate-spin text-brand-500" />
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Newspaper className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No reports yet. Generate your first newspaper!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 bg-slate-800 rounded-xl"
                >
                  <div>
                    <div className="font-medium">Daily Brief #{report.id}</div>
                    <div className="text-sm text-slate-400">{formatDate(report.generated_at)}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {report.pdf_path && (
                      <button
                        onClick={() => reportsAPI.download(report.id)}
                        className="p-2 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        <Download className="w-5 h-5" />
                      </button>
                    )}
                    <Link
                      to={`/reports/${report.id}`}
                      className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
