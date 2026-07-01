import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight, Brain, Search, FileText } from 'lucide-react'

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative flex min-h-screen items-center justify-center px-lg py-3xl">
        <div className="max-w-5xl text-center">
          <h1 className="text-display-lg md:text-display-lg-mobile font-bold text-foreground mb-6">
            Clinical Intelligence
            <span className="block text-primary-container">Powered by AI</span>
          </h1>
          <p className="text-body-lg text-muted-foreground mb-8 max-w-3xl mx-auto">
            MedNexus AI delivers evidence-based medical knowledge through advanced RAG technology,
            empowering healthcare professionals with instant access to clinical insights.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link to="/register">
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/login">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-lg py-3xl bg-surface-container">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-headline-md text-center mb-2xl">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-lg">
            <FeatureCard
              icon={<Brain />}
              title="AI Medical Assistant"
              description="Ask questions and receive evidence-based answers with citations."
            />
            <FeatureCard
              icon={<Search />}
              title="Knowledge Search"
              description="Hybrid vector search across medical literature and clinical guidelines."
            />
            <FeatureCard
              icon={<FileText />}
              title="Report Analysis"
              description="Upload medical reports for AI-powered analysis and insights."
            />
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-lg rounded-xl border border-border bg-surface-glass backdrop-blur-glass hover:border-primary/40 transition-all">
      <div className="mb-4 text-primary-container">{icon}</div>
      <h3 className="text-headline-md font-semibold mb-2">{title}</h3>
      <p className="text-body-md text-muted-foreground">{description}</p>
    </div>
  )
}
