/**
 * NewsMind AI - Preferences Page
 */

import { useState, useEffect } from 'react';
import { Save, Plus, X, Loader, AlertCircle, CheckCircle } from 'lucide-react';
import { preferencesAPI } from '../../services/api';

export default function Preferences() {
  const [interests, setInterests] = useState([]);
  const [sources, setSources] = useState([]);
  const [excluded, setExcluded] = useState([]);
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [newInterest, setNewInterest] = useState('');
  const [newSource, setNewSource] = useState('');
  const [newExcluded, setNewExcluded] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [prefRes, interestsRes, sourcesRes, excludedRes] = await Promise.all([
        preferencesAPI.get(),
        preferencesAPI.getInterests(),
        preferencesAPI.getSources(),
        preferencesAPI.getExcluded(),
      ]);
      setPreferences(prefRes.data);
      setInterests(interestsRes.data);
      setSources(sourcesRes.data);
      setExcluded(excludedRes.data);
    } catch (err) {
      setError('Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const addInterest = async () => {
    if (!newInterest.trim()) return;
    try {
      await preferencesAPI.addInterest(newInterest.trim());
      await loadData();
      setNewInterest('');
    } catch (err) {
      setError('Failed to add interest');
    }
  };

  const removeInterest = async (id) => {
    try {
      await preferencesAPI.removeInterest(id);
      setInterests(interests.filter((i) => i.id !== id));
    } catch (err) {
      setError('Failed to remove interest');
    }
  };

  const addSource = async () => {
    if (!newSource.trim()) return;
    try {
      await preferencesAPI.addSource(newSource.trim());
      await loadData();
      setNewSource('');
    } catch (err) {
      setError('Failed to add source');
    }
  };

  const removeSource = async (id) => {
    try {
      await preferencesAPI.removeSource(id);
      setSources(sources.filter((s) => s.id !== id));
    } catch (err) {
      setError('Failed to remove source');
    }
  };

  const addExcluded = async () => {
    if (!newExcluded.trim()) return;
    try {
      await preferencesAPI.addExcluded(newExcluded.trim());
      await loadData();
      setNewExcluded('');
    } catch (err) {
      setError('Failed to add excluded topic');
    }
  };

  const removeExcluded = async (id) => {
    try {
      await preferencesAPI.removeExcluded(id);
      setExcluded(excluded.filter((t) => t.id !== id));
    } catch (err) {
      setError('Failed to remove excluded topic');
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    setSuccess('');
    try {
      await preferencesAPI.update(preferences);
      setSuccess('Preferences saved!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to save preferences');
    } finally {
      setSaving(false);
    }
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
        <h1 className="text-2xl font-bold mb-6">Preferences</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            {error}
            <button onClick={() => setError('')} className="ml-auto">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center gap-3 text-emerald-400">
            <CheckCircle className="w-5 h-5" />
            {success}
          </div>
        )}

        {/* Reading Preferences */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Reading Preferences</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Reading Style</label>
              <select
                value={preferences.reading_style || 'bullet_points'}
                onChange={(e) => setPreferences({ ...preferences, reading_style: e.target.value })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
              >
                <option value="bullet_points">Bullet Points</option>
                <option value="narrative">Narrative</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Language</label>
              <select
                value={preferences.preferred_language || 'en'}
                onChange={(e) => setPreferences({ ...preferences, preferred_language: e.target.value })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            </div>
          </div>
          <button
            onClick={handleSavePreferences}
            disabled={saving}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-50"
          >
            {saving ? <Loader className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
            Save Preferences
          </button>
        </div>

        {/* Interests */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Interests</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {interests.map((interest) => (
              <span
                key={interest.id}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-brand-500/20 text-brand-300 rounded-full"
              >
                {interest.topic}
                <button onClick={() => removeInterest(interest.id)}>
                  <X className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newInterest}
              onChange={(e) => setNewInterest(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addInterest()}
              placeholder="Add interest..."
              className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
            />
            <button onClick={addInterest} className="p-2 bg-brand-500 rounded-xl hover:bg-brand-600">
              <Plus className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Preferred Sources */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Preferred Sources</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {sources.map((source) => (
              <span
                key={source.id}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-500/20 text-indigo-300 rounded-full"
              >
                {source.topic}
                <button onClick={() => removeSource(source.id)}>
                  <X className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newSource}
              onChange={(e) => setNewSource(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addSource()}
              placeholder="Add source..."
              className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
            />
            <button onClick={addSource} className="p-2 bg-indigo-500 rounded-xl hover:bg-indigo-600">
              <Plus className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Excluded Topics */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-lg font-semibold mb-4">Topics to Exclude</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {excluded.map((topic) => (
              <span
                key={topic.id}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-500/20 text-red-300 rounded-full"
              >
                {topic.topic}
                <button onClick={() => removeExcluded(topic.id)}>
                  <X className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newExcluded}
              onChange={(e) => setNewExcluded(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addExcluded()}
              placeholder="Add topic to exclude..."
              className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
            />
            <button onClick={addExcluded} className="p-2 bg-red-500 rounded-xl hover:bg-red-600">
              <Plus className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
