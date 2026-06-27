/**
 * NewsMind AI - Landing Page
 */

import { Link } from 'react-router-dom';
import { Newspaper, Zap, Brain, Mail, Shield, Clock } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600/20 to-indigo-600/20" />
        <div className="relative max-w-6xl mx-auto px-6 py-20">
          <div className="text-center space-y-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-600 shadow-lg shadow-brand-500/30">
              <Newspaper className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-5xl font-extrabold tracking-tight">
              <span className="bg-gradient-to-r from-brand-400 to-indigo-400 bg-clip-text text-transparent">
                NewsMind AI
              </span>
            </h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Your Personal Intelligence Agent. Get a customized daily newspaper powered by AI, 
              tailored to your interests, delivered to your inbox.
            </p>
            <div className="flex justify-center gap-4 pt-4">
              <Link
                to="/register"
                className="px-8 py-3 rounded-xl bg-gradient-to-r from-brand-500 to-indigo-500 text-white font-semibold hover:from-brand-600 hover:to-indigo-600 transition-all shadow-lg shadow-brand-500/25"
              >
                Get Started
              </Link>
              <Link
                to="/login"
                className="px-8 py-3 rounded-xl border border-slate-700 text-slate-300 font-semibold hover:bg-slate-800 transition-all"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">
          Powered by Agentic AI
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Brain className="w-6 h-6" />}
            title="LangGraph Agents"
            description="Five specialized AI agents work together to research, curate, and deliver your personalized news."
          />
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="MCP Tools"
            description="Model Context Protocol enables seamless integration with news APIs, GitHub, and weather services."
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6" />}
            title="Local LLMs"
            description="Powered by Ollama for privacy-first AI processing on your own infrastructure."
          />
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-slate-900/50 border-y border-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <StepCard number={1} title="Sign Up" description="Create your account and verify your email." />
            <StepCard number={2} title="Set Preferences" description="Choose your interests and preferred sources." />
            <StepCard number={3} title="AI Generates" description="Our agents curate and summarize your daily brief." />
            <StepCard number={4} title="Get Delivered" description="Receive your personalized newspaper via email." />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-slate-500">
          <p>Built with React, FastAPI, LangGraph, MCP, and Ollama</p>
          <p className="mt-2 text-sm">A demonstration of Agentic AI architecture</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-brand-500/50 transition-colors">
      <div className="w-12 h-12 rounded-xl bg-brand-500/20 text-brand-400 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 text-sm">{description}</p>
    </div>
  );
}

function StepCard({ number, title, description }) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-brand-500 text-white flex items-center justify-center mx-auto mb-4 font-bold text-lg">
        {number}
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 text-sm">{description}</p>
    </div>
  );
}
