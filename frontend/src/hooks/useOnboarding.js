/**
 * NewsMind AI - Onboarding Hook
 * Manages onboarding state and form data.
 */

import { useState, useCallback } from 'react';
import { preferencesAPI } from '../services/api';

const INTEREST_OPTIONS = [
  'Artificial Intelligence',
  'Machine Learning',
  'Web Development',
  'Mobile Development',
  'DevOps',
  'Cloud Computing',
  'Cybersecurity',
  'Data Science',
  'Blockchain',
  'IoT',
  'Programming',
  'Startups',
  'Productivity',
  'Career',
  'Science',
  'Technology News',
];

const SOURCE_OPTIONS = [
  'Hacker News',
  'Reddit Technology',
  'Ars Technica',
  'GitHub Trending',
  'Dev.to',
  'Medium',
  'TechCrunch',
  'Wired',
];

const READING_STYLES = [
  { value: 'bullet_points', label: 'Bullet Points' },
  { value: 'narrative', label: 'Narrative' },
  { value: 'detailed', label: 'Detailed Analysis' },
];

const FREQUENCY_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekdays', label: 'Weekdays Only' },
  { value: 'weekends', label: 'Weekends Only' },
  { value: 'weekly', label: 'Weekly' },
];

const TIME_OPTIONS = [
  '06:00', '07:00', '08:00', '09:00', '10:00',
  '11:00', '12:00', '13:00', '14:00', '15:00',
  '16:00', '17:00', '18:00', '19:00', '20:00',
];

export function useOnboarding() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    interests: [],
    customInterests: [],
    excludedTopics: [],
    preferredSources: [],
    readingStyle: 'bullet_points',
    deliveryTime: '08:00',
    deliveryFrequency: 'daily',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'ist',
    preferredLanguage: 'en',
  });

  const toggleInterest = useCallback((interest) => {
    setData((prev) => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest],
    }));
  }, []);

  const addCustomInterest = useCallback((interest) => {
    if (interest && !data.customInterests.includes(interest)) {
      setData((prev) => ({
        ...prev,
        customInterests: [...prev.customInterests, interest],
      }));
    }
  }, [data.customInterests]);

  const removeCustomInterest = useCallback((interest) => {
    setData((prev) => ({
      ...prev,
      customInterests: prev.customInterests.filter((i) => i !== interest),
    }));
  }, []);

  const toggleSource = useCallback((source) => {
    setData((prev) => ({
      ...prev,
      preferredSources: prev.preferredSources.includes(source)
        ? prev.preferredSources.filter((s) => s !== source)
        : [...prev.preferredSources, source],
    }));
  }, []);

  const toggleExcludedTopic = useCallback((topic) => {
    setData((prev) => ({
      ...prev,
      excludedTopics: prev.excludedTopics.includes(topic)
        ? prev.excludedTopics.filter((t) => t !== topic)
        : [...prev.excludedTopics, topic],
    }));
  }, []);

  const updateData = useCallback((updates) => {
    setData((prev) => ({ ...prev, ...updates }));
  }, []);

  const submitOnboarding = useCallback(async (userName, userEmail) => {
    setLoading(true);
    setError(null);
    try {
      await preferencesAPI.completeOnboarding({
        name: userName,
        email: userEmail,
        interests: data.interests,
        custom_interests: data.customInterests,
        excluded_topics: data.excludedTopics,
        preferred_sources: data.preferredSources,
        reading_style: data.readingStyle,
        delivery_time: data.deliveryTime,
        delivery_frequency: data.deliveryFrequency,
        timezone: data.timezone,
        preferred_language: data.preferredLanguage,
      });
      return { success: true };
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save preferences');
      return { success: false, error: err };
    } finally {
      setLoading(false);
    }
  }, [data]);

  const nextStep = useCallback(() => setStep((s) => s + 1), []);
  const prevStep = useCallback(() => setStep((s) => Math.max(0, s - 1)), []);

  return {
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
  };
}
