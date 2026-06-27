/**
 * NewsMind AI - Onboarding Page
 * Multi-step onboarding wizard for new users.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Loader, X, Plus } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useOnboarding } from '../../hooks/useOnboarding';

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const {
    step,
    data,
    loading,
    error,
    nextStep,
    prevStep,
    toggleInterest,
    addCustomInterest,
    removeCustomInterest,
    toggleSource,
    toggleExcludedTopic,
    updateData,
    submitOnboarding,
    INTEREST_OPTIONS,
    SOURCE_OPTIONS,
    READING_STYLES,
    FREQUENCY_OPTIONS,
    TIME_OPTIONS,
  } = useOnboarding();

  const [customInput, setCustomInput] = useState('');

  const handleSubmit = async () => {
    const result = await submitOnboarding(user?.name || 'User', user?.email || '');
    if (result.success) {
      navigate('/dashboard');
    }
  };

  const handleAddCustom = () => {
    if (customInput.trim()) {
      addCustomInterest(customInput.trim());
      setCustomInput('');
    }
  };

  const steps = [
    <InterestsStep
      key="interests"
      data={data}
      toggleInterest={toggleInterest}
      customInput={customInput}
      setCustomInput={setCustomInput}
      handleAddCustom={handleAddCustom}
      removeCustomInterest={removeCustomInterest}
      options={INTEREST_OPTIONS}
    />,
    <SourcesStep key="sources" data={data} toggleSource={toggleSource} options={SOURCE_OPTIONS} />,
    <PreferencesStep
      key="preferences"
      data={data}
      updateData={updateData}
      toggleExcludedTopic={toggleExcludedTopic}
      readingStyles={READING_STYLES}
      frequencyOptions={FREQUENCY_OPTIONS}
      timeOptions={TIME_OPTIONS}
    />,
    <SummaryStep key="summary" data={data} />,
  ];

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`flex-1 h-2 mx-1 rounded-full ${
                  s <= step + 1 ? 'bg-brand-500' : 'bg-slate-700'
                }`}
              />
            ))}
          </div>
          <div className="text-center text-sm text-slate-400">
            Step {step + 1} of 4
          </div>
        </div>

        {/* Content */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          {steps[step]}

          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <button
              onClick={prevStep}
              disabled={step === 0}
              className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
              Back
            </button>

            {step < 3 ? (
              <button
                onClick={nextStep}
                className="flex items-center gap-2 px-6 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-colors"
              >
                Next
                <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-brand-500 to-indigo-500 text-white rounded-xl hover:from-brand-600 hover:to-indigo-600 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Complete Setup'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InterestsStep({ data, toggleInterest, customInput, setCustomInput, handleAddCustom, removeCustomInterest, options }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Select Your Interests</h2>
      <p className="text-slate-400 mb-6">Choose topics you'd like to see in your daily brief.</p>

      <div className="flex flex-wrap gap-2 mb-4">
        {options.map((interest) => (
          <button
            key={interest}
            onClick={() => toggleInterest(interest)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              data.interests.includes(interest)
                ? 'bg-brand-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {interest}
          </button>
        ))}
      </div>

      {/* Custom interests */}
      <div className="mt-6">
        <label className="block text-sm font-medium mb-2">Add Custom Interest</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddCustom()}
            placeholder="e.g., Rust Programming"
            className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={handleAddCustom}
            className="px-4 py-2 bg-brand-500 text-white rounded-xl hover:bg-brand-600"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        {data.customInterests.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {data.customInterests.map((interest) => (
              <span
                key={interest}
                className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-sm"
              >
                {interest}
                <button onClick={() => removeCustomInterest(interest)}>
                  <X className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SourcesStep({ data, toggleSource, options }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Preferred Sources</h2>
      <p className="text-slate-400 mb-6">Select your trusted news sources.</p>

      <div className="flex flex-wrap gap-2">
        {options.map((source) => (
          <button
            key={source}
            onClick={() => toggleSource(source)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              data.preferredSources.includes(source)
                ? 'bg-brand-500 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {source}
          </button>
        ))}
      </div>
    </div>
  );
}

function PreferencesStep({ data, updateData, toggleExcludedTopic, readingStyles, frequencyOptions, timeOptions }) {
  const excludeOptions = ['Politics', 'Sports', 'Celebrity News', 'Gossip', 'Crypto Speculation'];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Delivery Preferences</h2>
      <p className="text-slate-400 mb-6">Customize how you receive your news.</p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Reading Style</label>
          <div className="flex gap-2">
            {readingStyles.map((style) => (
              <button
                key={style.value}
                onClick={() => updateData({ readingStyle: style.value })}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  data.readingStyle === style.value
                    ? 'bg-brand-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {style.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Delivery Time</label>
            <select
              value={data.deliveryTime}
              onChange={(e) => updateData({ deliveryTime: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:border-brand-500"
            >
              {timeOptions.map((time) => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Frequency</label>
            <select
              value={data.deliveryFrequency}
              onChange={(e) => updateData({ deliveryFrequency: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:border-brand-500"
            >
              {frequencyOptions.map((freq) => (
                <option key={freq.value} value={freq.value}>
                  {freq.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Topics to Exclude</label>
          <div className="flex flex-wrap gap-2">
            {excludeOptions.map((topic) => (
              <button
                key={topic}
                onClick={() => toggleExcludedTopic(topic)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  data.excludedTopics.includes(topic)
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryStep({ data }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Review Your Preferences</h2>
      <p className="text-slate-400 mb-6">Here's what we'll use to personalize your news.</p>

      <div className="space-y-4">
        <div className="bg-slate-800 rounded-xl p-4">
          <h3 className="font-medium text-brand-400 mb-2">Interests ({data.interests.length + data.customInterests.length})</h3>
          <div className="flex flex-wrap gap-2">
            {[...data.interests, ...data.customInterests].map((i) => (
              <span key={i} className="px-2 py-1 bg-slate-700 rounded text-sm">
                {i}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-4">
          <h3 className="font-medium text-brand-400 mb-2">Preferred Sources ({data.preferredSources.length})</h3>
          <div className="flex flex-wrap gap-2">
            {data.preferredSources.map((s) => (
              <span key={s} className="px-2 py-1 bg-slate-700 rounded text-sm">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-sm text-slate-400">Reading Style</div>
            <div className="font-medium capitalize">{data.readingStyle.replace('_', ' ')}</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-sm text-slate-400">Delivery Time</div>
            <div className="font-medium">{data.deliveryTime}</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-4 text-center">
            <div className="text-sm text-slate-400">Frequency</div>
            <div className="font-medium capitalize">{data.deliveryFrequency}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
