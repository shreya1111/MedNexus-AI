import Link from 'next/link';
import { Activity, Brain, Shield, TrendingUp, FileText, Users, ArrowRight, CheckCircle } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-gray-900">MedNexus AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">Sign in</Link>
            <Link href="/register" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-1.5 text-sm text-blue-700">
            <Brain className="h-4 w-4" />
            <span>Powered by LangChain RAG + Gemini AI</span>
          </div>
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            Healthcare Intelligence,{' '}
            <span className="text-blue-600">Reimagined</span>
          </h1>
          <p className="mb-10 mx-auto max-w-2xl text-lg text-gray-600">
            MedNexus AI combines RAG-powered medical Q&amp;A, ML diagnostics, and comprehensive patient management into one unified platform.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register" className="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3.5 text-base font-semibold text-white hover:bg-blue-700 transition-colors">
              Start for free <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/login" className="rounded-xl border border-gray-200 px-8 py-3.5 text-base font-semibold text-gray-700 hover:bg-gray-50 transition-colors">
              Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50 px-4">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">Everything you need, in one place</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: Brain, title: 'AI Medical Q&A', desc: 'Ask medical questions and get evidence-based answers powered by RAG over your own health documents.' },
              { icon: FileText, title: 'Medical Records', desc: 'Securely store, search, and summarize prescriptions, lab results, imaging reports, and more.' },
              { icon: TrendingUp, title: 'ML Diagnostics', desc: 'Predictive models for diabetes, heart disease, and other conditions trained on clinical datasets.' },
              { icon: Shield, title: 'HIPAA-grade Security', desc: 'End-to-end encryption, JWT authentication, RBAC, and rate limiting protect your sensitive data.' },
              { icon: Users, title: 'Multi-role Access', desc: 'Separate portals for patients, doctors, and admins with role-based permissions.' },
              { icon: Activity, title: 'Real-time Analytics', desc: 'Interactive dashboards tracking disease trends, appointment stats, and AI usage metrics.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                  <Icon className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="mb-2 font-semibold text-gray-900">{title}</h3>
                <p className="text-sm text-gray-600">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="py-20 px-4">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-8 text-center text-3xl font-bold text-gray-900">Production-Grade Stack</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              'Next.js 14 + TypeScript + Tailwind',
              'Express + MongoDB + Redis',
              'LangChain + Pinecone + OpenAI',
              'Scikit-learn + TensorFlow ML models',
              'Docker + NGINX + GitHub Actions CI/CD',
              'MLflow + DVC + Evidently AI MLOps',
              'Prometheus + Grafana monitoring',
              'JWT + bcrypt + Helmet security',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-lg border border-gray-100 px-4 py-3">
                <CheckCircle className="h-4 w-4 shrink-0 text-emerald-500" />
                <span className="text-sm text-gray-700">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-600 px-4 text-center">
        <h2 className="mb-4 text-3xl font-bold text-white">Ready to transform healthcare with AI?</h2>
        <p className="mb-8 text-blue-100">Join MedNexus AI and experience the future of patient care.</p>
        <Link href="/register" className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-blue-600 hover:bg-blue-50 transition-colors">
          Get started free <ArrowRight className="h-5 w-5" />
        </Link>
      </section>

      <footer className="border-t border-gray-100 py-8 px-4 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} MedNexus AI. Built with ❤️ as a full-stack AI portfolio project.
      </footer>
    </div>
  );
}
