/**
 * NewsMind AI - Schedule Page
 */

import { useState, useEffect } from 'react';
import { Plus, Trash2, Loader, AlertCircle, Clock } from 'lucide-react';
import { schedulesAPI } from '../../services/api';

const FREQUENCY_OPTIONS = [
  { value: 'daily', label: 'Every Day' },
  { value: 'weekdays', label: 'Weekdays Only' },
  { value: 'weekends', label: 'Weekends Only' },
  { value: 'weekly', label: 'Once a Week (Monday)' },
];

const TIME_OPTIONS = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);

export default function Schedule() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    delivery_time: '08:00',
    frequency: 'daily',
  });

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      const { data } = await schedulesAPI.get();
      setSchedules(data);
    } catch (err) {
      setError('Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await schedulesAPI.create(formData);
      await loadSchedules();
      setShowForm(false);
      setFormData({ delivery_time: '08:00', frequency: 'daily' });
    } catch (err) {
      setError('Failed to create schedule');
    }
  };

  const handleDelete = async (id) => {
    try {
      await schedulesAPI.delete(id);
      setSchedules(schedules.filter((s) => s.id !== id));
    } catch (err) {
      setError('Failed to delete schedule');
    }
  };

  const getFrequencyLabel = (value) => {
    return FREQUENCY_OPTIONS.find((f) => f.value === value)?.label || value;
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
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Delivery Schedule</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600"
          >
            <Plus className="w-5 h-5" />
            Add Schedule
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {showForm && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">New Schedule</h2>
            <form onSubmit={handleCreate}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Delivery Time</label>
                  <select
                    value={formData.delivery_time}
                    onChange={(e) => setFormData({ ...formData, delivery_time: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
                  >
                    {TIME_OPTIONS.map((time) => (
                      <option key={time} value={time}>
                        {time}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Frequency</label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
                  >
                    {FREQUENCY_OPTIONS.map((freq) => (
                      <option key={freq.value} value={freq.value}>
                        {freq.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600"
                >
                  Create Schedule
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 bg-slate-700 text-slate-300 rounded-xl hover:bg-slate-600"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {schedules.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Clock className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <p className="text-slate-400">No schedules configured yet.</p>
            <p className="text-slate-500 text-sm mt-2">Add a schedule to start receiving automated newspapers.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-brand-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-brand-400" />
                  </div>
                  <div>
                    <div className="font-semibold text-lg">{schedule.delivery_time}</div>
                    <div className="text-slate-400 text-sm">{getFrequencyLabel(schedule.frequency)}</div>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(schedule.id)}
                  className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <p className="text-slate-400 text-sm">
            Note: Scheduled delivery requires email configuration (SMTP) to be set up in the backend.
            Your newspaper will be generated and sent automatically at the specified times.
          </p>
        </div>
      </div>
    </div>
  );
}
