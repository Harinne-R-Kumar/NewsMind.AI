/**
 * NewsMind AI - Reports Page
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Newspaper, Download, Loader, Star } from 'lucide-react';
import { reportsAPI } from '../../services/api';

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const { data } = await reportsAPI.list();
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Generated Reports</h1>

        {reports.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Newspaper className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <p className="text-slate-400">No reports generated yet.</p>
            <p className="text-slate-500 text-sm mt-2">
              Generate your first newspaper from the dashboard.
            </p>
            <Link
              to="/dashboard"
              className="inline-block mt-4 px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600"
            >
              Go to Dashboard
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">Daily Brief #{report.id}</h3>
                      <p className="text-slate-400 text-sm mt-1">{formatDate(report.generated_at)}</p>
                    </div>
                    {report.overall_rating && (
                      <div className="flex items-center gap-1 text-amber-400">
                        <Star className="w-5 h-5 fill-current" />
                        <span>{report.overall_rating}/5</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <Link
                      to={`/reports/${report.id}`}
                      className="flex-1 text-center px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-colors"
                    >
                      View Report
                    </Link>
                    {report.pdf_path && (
                      <button
                        onClick={() => reportsAPI.download(report.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 transition-colors"
                      >
                        <Download className="w-5 h-5" />
                        PDF
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
