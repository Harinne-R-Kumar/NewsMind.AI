/**
 * NewsMind AI - Report Detail Page
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Download, Star, Loader, ThumbsUp, ThumbsDown } from 'lucide-react';
import { reportsAPI, feedbackAPI } from '../../services/api';

export default function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadReport();
  }, [id]);

  const loadReport = async () => {
    try {
      const { data } = await reportsAPI.get(id);
      setReport(data);
      setRating(data.overall_rating || 0);
      setFeedback(data.overall_feedback || '');
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async () => {
    if (!rating && !feedback) return;
    setSubmitting(true);
    try {
      await feedbackAPI.submitReport(id, {
        overall_rating: rating || null,
        overall_feedback: feedback || null,
      });
      alert('Thank you for your feedback!');
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-slate-400">Report not found</p>
          <Link to="/reports" className="text-brand-400 hover:underline mt-4 inline-block">
            Back to Reports
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link
            to="/reports"
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Reports
          </Link>
          {report.pdf_path && (
            <button
              onClick={() => reportsAPI.download(id)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 transition-colors"
            >
              <Download className="w-5 h-5" />
              Download PDF
            </button>
          )}
        </div>

        {/* Report Content */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div
            className="prose prose-invert max-w-none p-6"
            dangerouslySetInnerHTML={{ __html: report.html_content }}
          />
        </div>

        {/* Feedback Section */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6">
          <h3 className="text-lg font-semibold mb-4">Rate This Report</h3>

          <div className="flex items-center gap-2 mb-4">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setRating(star)}
                className={`p-1 rounded transition-colors ${
                  star <= rating ? 'text-amber-400' : 'text-slate-600 hover:text-amber-400'
                }`}
              >
                <Star className="w-8 h-8 fill-current" />
              </button>
            ))}
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Additional Feedback (Optional)</label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Tell us what you think..."
              rows={3}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:border-brand-500 resize-none"
            />
          </div>

          <button
            onClick={submitFeedback}
            disabled={submitting || (!rating && !feedback)}
            className="px-6 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      </div>
    </div>
  );
}
